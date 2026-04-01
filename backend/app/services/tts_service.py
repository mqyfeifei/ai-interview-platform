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


# 环境配置提取
VOLC_APP_ID = os.environ.get('VOLC_APP_ID', '你的App ID')
VOLC_ACCESS_TOKEN = os.environ.get('VOLC_ACCESS_TOKEN', '你的Access Token')
VOLC_SECRET_KEY = os.environ.get('VOLC_SECRET_KEY', '你的Secret Key')
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
        if USE_VOLC:
            try:
                data = cls._synthesize_volc(text, voice, fmt)
                if data:
                    return data
            except Exception as e:
                # Don't fail hard; fall back to local
                print("Volc TTS failed, falling back to local TTS:", e)

        return cls._synthesize_local(text, voice, fmt)

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
        """
        调用火山引擎 TTS 2.0 (豆包大模型语音合成)
        采用 Bearer Token 鉴权，避开复杂的 AK/SK 签名。
        """
        if not text.strip():
            return None

        # 火山 TTS 标准请求地址
        url = "https://openspeech.bytedance.com/api/v1/tts"

        # 默认使用豆包通用男声(最适合面试官的声音)
        target_voice = voice if voice else "BV001_streaming"

        headers = {
            "Authorization": f"Bearer {VOLC_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "app": {
                "appid": VOLC_APP_ID,
                "token": VOLC_ACCESS_TOKEN,
                "cluster": "volcano_tts" # 豆包大模型 TTS 对应的标准集群
            },
            "user": {
                "uid": "ai_interviewer_backend"
            },
            "audio": {
                "voice_type": target_voice,
                "encoding": "mp3", # 前端直接使用 audio 标签或 AudioContext 播放 MP3 兼容性最好
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0
            },
            "request": {
                "reqid": "req_" + os.urandom(8).hex(), # 随机生成请求 ID 以便日志追踪
                "text": text,
                "text_type": "plain",
                "operation": "query"
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            res_json = response.json()

            if res_json.get("code") == 3000:
                # 火山接口返回的 data 是 base64 编码的音频字符串，我们需要将其解码为 bytes 返回
                audio_base64 = res_json.get("data")
                if audio_base64:
                    return base64.b64decode(audio_base64)
            else:
                print(f"VolcEngine TTS 业务报错: {res_json.get('message')}")
                return None

        except Exception as e:
            print(f"VolcEngine TTS 请求异常: {str(e)}")
            raise e

# Helper: encode bytes as base64 text to send over SSE/JSON
def bytes_to_b64(data_bytes):
    return base64.b64encode(data_bytes).decode('ascii')
