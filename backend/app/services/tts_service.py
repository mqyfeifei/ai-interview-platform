# backend/app/services/tts_service.py
"""
TTSService
- Provides a simple, runnable fallback TTS implementation using pyttsx3 (offline).
- Exposes a hook `synthesize_bytes(text, voice=None, fmt='wav') -> bytes` that returns audio bytes.
- If you later want to enable VolcEngine TTS, implement `_synthesize_volc` using the provided
  VOLC_APP_ID / VOLC_ACCESS_TOKEN / VOLC_SECRET_KEY environment variables and set
  USE_VOLC=1 in env; the service will try Volc first and fall back to local pyttsx3.

Notes:
- This file is intentionally self-contained and safe to run locally for development/testing.
- The api surface is kept minimal so it can be integrated into streaming code: for each
  small text chunk we synthesize a short WAV and return its bytes (base64-encodable).
"""
import os
import json
import uuid
import struct
import tempfile
import base64
import threading
import requests

from io import BytesIO

# Local TTS fallback uses pyttsx3 which is fully offline.
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import websocket
except Exception:
    websocket = None


# 环境配置提取
VOLC_APP_ID = os.environ.get('VOLC_APP_ID', '你的App ID')
VOLC_ACCESS_TOKEN = os.environ.get('VOLC_ACCESS_TOKEN', '你的Access Token')
VOLC_SECRET_KEY = os.environ.get('VOLC_SECRET_KEY', '你的Secret Key')
VOLC_RESOURCE_ID = os.environ.get('VOLC_RESOURCE_ID', 'volc.service_type.10029')
VOLC_TTS_WS_URL = os.environ.get('VOLC_TTS_WS_URL', 'wss://openspeech.bytedance.com/api/v3/tts/bidirection')
VOLC_TTS_SPEAKER = os.environ.get('VOLC_TTS_SPEAKER', 'BV001_streaming')
USE_VOLC = os.environ.get('USE_VOLC', '0') == '1'


class TTSService:
    """Provides synthesize_bytes(text) -> bytes

    For streaming usage, callers should call synthesize_bytes repeatedly for
    incoming small text chunks and immediately relay the returned audio bytes
    to the client (e.g., via SSE or WebSocket). This approximates real-time
    "边生成边播放" behavior without requiring a WebSocket-based TTS.
    """

    _engine = None
    _engine_lock = threading.Lock()
    _EVENT_START_CONNECTION = 1
    _EVENT_FINISH_CONNECTION = 2
    _EVENT_START_SESSION = 100
    _EVENT_FINISH_SESSION = 102
    _EVENT_TASK_REQUEST = 200
    _EVENT_TTS_SENTENCE_START = 350
    _EVENT_TTS_SENTENCE_END = 351
    _EVENT_TTS_RESPONSE = 352
    _EVENT_CONNECTION_STARTED = 50
    _EVENT_SESSION_STARTED = 150
    _EVENT_SESSION_FINISHED = 152

    @classmethod
    def _ensure_engine(cls):
        if pyttsx3 is None:
            raise RuntimeError('pyttsx3 is required for local TTS fallback. Install with `pip install pyttsx3`')
        if cls._engine is None:
            with cls._engine_lock:
                if cls._engine is None:
                    cls._engine = pyttsx3.init()
        return cls._engine

    @classmethod
    def synthesize_bytes(cls, text, voice=None, fmt='wav'):
        """Synthesize `text` to audio bytes. By default uses local pyttsx3.

        If USE_VOLC is true, this function will try to call VolcEngine (placeholder)
        and fall back to local TTS on any failure.
        """
        safe_fmt = (fmt or 'mp3').lower()
        if safe_fmt == 'wav':
            safe_fmt = 'mp3'

        if USE_VOLC:
            try:
                data = cls._synthesize_volc(text, voice, safe_fmt)
                if data:
                    return data
            except Exception as e:
                # Don't fail hard; fall back to local
                print("Volc TTS failed, falling back to local TTS:", e)

        return cls._synthesize_local(text, voice, safe_fmt if safe_fmt in ('wav', 'mp3') else 'wav')

    @classmethod
    def _synthesize_local(cls, text, voice, fmt='wav'):
        """Local pyttsx3 synthesize to WAV bytes."""
        engine = cls._ensure_engine()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + fmt) as tmp:
            tmp_path = tmp.name
        try:
            # pyttsx3 provides save_to_file API
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            with open(tmp_path, 'rb') as f:
                data = f.read()
            return data
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    @classmethod
    def _synthesize_volc(cls, text, voice=None, fmt='mp3'):
        """调用豆包 TTS V3 双向流式 WebSocket。"""
        if not text.strip():
            return None
        if websocket is None:
            raise RuntimeError('websocket-client not installed')
        if not VOLC_APP_ID or '你的App ID' in VOLC_APP_ID:
            raise RuntimeError('VOLC_APP_ID not configured')
        if not VOLC_ACCESS_TOKEN or '你的Access Token' in VOLC_ACCESS_TOKEN:
            raise RuntimeError('VOLC_ACCESS_TOKEN not configured')
        if not VOLC_RESOURCE_ID:
            raise RuntimeError('VOLC_RESOURCE_ID not configured')

        target_voice = voice if voice else VOLC_TTS_SPEAKER
        target_fmt = (fmt or 'mp3').lower()
        if target_fmt == 'wav':
            target_fmt = 'mp3'
        if target_fmt not in ('mp3', 'pcm', 'ogg_opus'):
            target_fmt = 'mp3'

        connect_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        ws = None
        audio_parts = []
        try:
            ws = websocket.create_connection(
                VOLC_TTS_WS_URL,
                timeout=15,
                header=[
                    f"X-Api-App-Key: {VOLC_APP_ID}",
                    f"X-Api-Access-Key: {VOLC_ACCESS_TOKEN}",
                    f"X-Api-Resource-Id: {VOLC_RESOURCE_ID}",
                    f"X-Api-Connect-Id: {connect_id}",
                ],
            )

            ws.send_binary(cls._pack_frame(cls._EVENT_START_CONNECTION, connect_id, {"event": "StartConnection"}))
            cls._wait_for_event(ws, cls._EVENT_CONNECTION_STARTED)

            session_meta = {
                "tts_session_meta": {
                    "session_id": session_id,
                    "req_params": {
                        "speaker": target_voice,
                        "audio_params": {
                            "format": target_fmt,
                            "sample_rate": 24000,
                        },
                    },
                }
            }
            ws.send_binary(cls._pack_frame(cls._EVENT_START_SESSION, session_id, session_meta))
            cls._wait_for_event(ws, cls._EVENT_SESSION_STARTED)

            task_payload = {
                "text": text,
                "text_type": "plain",
            }
            ws.send_binary(cls._pack_frame(cls._EVENT_TASK_REQUEST, session_id, task_payload))
            ws.send_binary(cls._pack_frame(cls._EVENT_FINISH_SESSION, session_id, {"event": "FinishSession"}))

            while True:
                event, _, payload = cls._recv_frame(ws)
                if event == cls._EVENT_TTS_RESPONSE and payload:
                    audio_parts.append(payload)
                if event == cls._EVENT_SESSION_FINISHED:
                    break

            ws.send_binary(cls._pack_frame(cls._EVENT_FINISH_CONNECTION, connect_id, {"event": "FinishConnection"}))
            return b"".join(audio_parts) if audio_parts else None
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    @classmethod
    def _pack_frame(cls, event, identity, payload_obj=None):
        payload = b""
        if payload_obj is not None:
            payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
        identity_bytes = (identity or "").encode("utf-8")
        header = bytes([0x11, 0x00, 0x10 if payload else 0x00, 0x00])
        return (
            header
            + struct.pack(">I", int(event))
            + struct.pack(">I", len(identity_bytes))
            + identity_bytes
            + struct.pack(">I", len(payload))
            + payload
        )

    @classmethod
    def _recv_frame(cls, ws):
        message = ws.recv()
        if isinstance(message, str):
            message = message.encode("utf-8")
        if not message or len(message) < 12:
            raise RuntimeError("invalid TTS frame")

        event = struct.unpack(">I", message[4:8])[0]
        id_len = struct.unpack(">I", message[8:12])[0]
        cursor = 12
        identity = ""
        if id_len > 0:
            identity = message[cursor:cursor + id_len].decode("utf-8", errors="ignore")
            cursor += id_len
        payload = b""
        if cursor + 4 <= len(message):
            payload_len = struct.unpack(">I", message[cursor:cursor + 4])[0]
            cursor += 4
            if payload_len < 0 or payload_len > 50 * 1024 * 1024:
                raise RuntimeError("invalid TTS payload length")
            if cursor + payload_len > len(message):
                raise RuntimeError("truncated TTS payload")
            payload = message[cursor:cursor + payload_len]
        return event, identity, payload

    @classmethod
    def _wait_for_event(cls, ws, expected_event):
        while True:
            event, _, _ = cls._recv_frame(ws)
            if event == expected_event:
                return

# Helper: encode bytes as base64 text to send over SSE/JSON
def bytes_to_b64(data_bytes):
    return base64.b64encode(data_bytes).decode('ascii')
