# backend/app/services/tts_service.py
"""
TTSService — 豆包 TTS V3 双向流式 WebSocket 实现（严格遵循官方协议规范）

协议要点：
- 通信地址: wss://openspeech.bytedance.com/api/v3/tts/bidirection
- 所有帧必须封装在自定义二进制帧格式中
- 状态机：StartConnection(1) → ConnectionStarted(50) → StartSession(100)
          → SessionStarted(150) → TaskRequest(200) ← [TTSResponse(352)]
          → FinishSession(102) → SessionFinished(152) → FinishConnection(2)

二进制帧头（4字节）：
  Byte 0: 0x11  — 协议版本v1，头部长度4
  Byte 1: 0x14  — MsgType=FullClientRequest(1<<4) | MsgTypeFlag=WithEvent(4)
  Byte 2: 0x10  — 序列化=JSON(1<<4) | 压缩=无(0)
  Byte 3: 0x00  — 保留位

帧结构（Byte1 含 WithEvent 标志时）:
  [4B Header] [4B EventNumber(big-endian int32)]
  对于连接事件 (event 1, 2):  [4B PayloadLen] [Payload]
  对于会话事件 (event 100, 102, 200): [4B SessionIdLen] [SessionId] [4B PayloadLen] [Payload]
"""
import os
import json
import uuid
import struct
import re
import tempfile
import base64
import threading
import time

from io import BytesIO

# 本地 TTS 降级方案（离线）
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import websocket
except Exception:
    websocket = None


# ──────────────────────────────────────────────
# 环境配置提取
# ──────────────────────────────────────────────
VOLC_APP_ID        = os.environ.get('VOLC_APP_ID', '')
VOLC_ACCESS_TOKEN  = os.environ.get('VOLC_ACCESS_TOKEN', '')
VOLC_RESOURCE_ID   = os.environ.get('VOLC_RESOURCE_ID', 'seed-tts-2.0')  # BigTTS 音色需要 seed-tts-2.0
VOLC_TTS_WS_URL    = os.environ.get('VOLC_TTS_WS_URL', 'wss://openspeech.bytedance.com/api/v3/tts/bidirection')
VOLC_TTS_SPEAKER   = os.environ.get('VOLC_TTS_SPEAKER', 'zh_female_shuangkuaisisi_uranus_bigtts')  # 爽快思思 2.0（来自官方文档确认的音色列表）
VOLC_TTS_LEGACY_SPEAKER = os.environ.get('VOLC_TTS_LEGACY_SPEAKER', 'BV001_streaming')
USE_VOLC           = os.environ.get('USE_VOLC', '0') == '1'
VOLC_STRICT_MODE   = os.environ.get('VOLC_STRICT_MODE', '0') == '1'
VOLC_RETRY_COOLDOWN_SECONDS = int(os.environ.get('VOLC_RETRY_COOLDOWN_SECONDS', '300'))

# 文档中的常见资源 ID：
# - seed-tts-2.0: 豆包语音合成模型 2.0
# - seed-tts-1.0 / volc.service_type.10029: 豆包语音合成模型 1.0
VOLC_RESOURCE_CANDIDATES = [
    VOLC_RESOURCE_ID,
    'seed-tts-2.0',
    'seed-tts-1.0',
    'seed-tts-1.0-concurr',
    'volc.service_type.10029',
    'volc.service_type.10048',
]

# 官方文档里可用于 seed-tts-2.0 的常见 2.0 音色。
# 这里保留一个较小但实用的候选集合，避免单个 speaker 在当前账号/资源下不可用时整条链路失败。
DEFAULT_VOLC_2_SPEAKER_CANDIDATES = [
    'zh_female_shuangkuaisisi_uranus_bigtts',
    'zh_female_xiaohe_uranus_bigtts',
    'zh_female_vv_uranus_bigtts',
    'zh_female_qingxinnvsheng_uranus_bigtts',
    'zh_female_tianmeixiaoyuan_uranus_bigtts',
    'zh_female_tianmeitaozi_uranus_bigtts',
    'zh_female_linjianvhai_uranus_bigtts',
    'zh_male_m191_uranus_bigtts',
    'zh_male_taocheng_uranus_bigtts',
    'zh_male_liufei_uranus_bigtts',
    'zh_male_sophie_uranus_bigtts',
]

# 兼容项目中的旧音色别名，统一映射到火山 2.0 的官方音色。
# 这样即便历史数据里仍然保存着旧值，也不会再把错误的 speaker 直接发给火山服务。
LEGACY_VOICE_ALIAS_MAP = {
    'BV001_streaming': VOLC_TTS_SPEAKER,
    'BV120_streaming': VOLC_TTS_SPEAKER,
}

KNOWN_VOLC_SPEAKERS = set(DEFAULT_VOLC_2_SPEAKER_CANDIDATES) | {VOLC_TTS_SPEAKER}
_SPEAKABLE_TEXT_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')


# ──────────────────────────────────────────────
# 二进制帧常量（严格按官方协议）
# ──────────────────────────────────────────────
# Byte 0: (Version=1 << 4) | (HeaderSize=1) = 0x11
_PROTO_VERSION_BYTE = 0x11
# Byte 1: (MsgType=FullClientRequest=1 << 4) | (MsgTypeFlag=WithEvent=4) = 0x14
_MSG_TYPE_BYTE      = 0x14
# Byte 2: (Serialization=JSON=1 << 4) | (Compression=None=0) = 0x10
_SERIAL_BYTE        = 0x10
# Byte 3: reserved
_RESERVED_BYTE      = 0x00

# 客户端发送的事件编号
_EVENT_START_CONNECTION  = 1
_EVENT_FINISH_CONNECTION = 2
_EVENT_START_SESSION     = 100
_EVENT_FINISH_SESSION    = 102
_EVENT_TASK_REQUEST      = 200

# 服务端返回的事件编号
_EVENT_CONNECTION_STARTED = 50
_EVENT_SESSION_STARTED    = 150
_EVENT_SESSION_FINISHED   = 152
_EVENT_TTS_SENTENCE_START = 350
_EVENT_TTS_SENTENCE_END   = 351
_EVENT_TTS_RESPONSE       = 352


# ──────────────────────────────────────────────
# 帧打包 / 解包工具
# ──────────────────────────────────────────────
def _build_header() -> bytes:
    """构建固定4字节帧头。"""
    return bytes([_PROTO_VERSION_BYTE, _MSG_TYPE_BYTE, _SERIAL_BYTE, _RESERVED_BYTE])


def _pack_connection_frame(event: int, payload_obj=None) -> bytes:
    """
    打包连接层事件帧 (event 1 / 2)。
    连接事件 **不携带** Session ID 字段，帧结构为：
      [4B Header] [4B Event] [4B PayloadLen] [Payload]
    """
    payload = b""
    if payload_obj is not None:
        payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    return (
        _build_header()
        + struct.pack(">i", event)
        + struct.pack(">I", len(payload))
        + payload
    )


def _pack_session_frame(event: int, session_id: str, payload_obj=None) -> bytes:
    """
    打包会话层事件帧 (event 100 / 102 / 200)。
    会话事件 **携带** Session ID 字段，帧结构为：
      [4B Header] [4B Event] [4B SessionIdLen] [SessionId] [4B PayloadLen] [Payload]
    """
    payload = b""
    if payload_obj is not None:
        payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    sid_bytes = (session_id or "").encode("utf-8")
    return (
        _build_header()
        + struct.pack(">i", event)
        + struct.pack(">I", len(sid_bytes))
        + sid_bytes
        + struct.pack(">I", len(payload))
        + payload
    )

def _recv_frame(ws) -> tuple:
    """
    接收并严格按火山引擎官方协议解析一帧服务端消息。
    返回: (event_id: int, session_id: str, payload: bytes)
    """
    message = ws.recv()
    if isinstance(message, str):
        message = message.encode("utf-8")

    if not message or len(message) < 4:
        raise RuntimeError(f"TTS 服务端返回帧过短: {len(message) if message else 0} bytes")

    # === 1. 协议头部解析 ===
    # Byte 0: 高4位是版本，低4位是头部长度（通常为 1，即 1 * 4 = 4 字节）
    header_size = (message[0] & 0x0F) * 4

    # Byte 1: 高4位是 MsgType(消息类型)，低4位是 Flags(特定标志)
    msg_type = (message[1] & 0xF0) >> 4
    msg_flags = message[1] & 0x0F

    cursor = header_size

    # === 2. 判断是否包含 Sequence Number ===
    # 如果 Flags 的最低位为 1，说明带有 4 字节的序列号，需要跳过
    if msg_flags & 0x01:
        cursor += 4

    # === 3. 根据 MsgType 分发处理 ===
    if msg_type == 11:
        # 【纯音频响应】Audio-only Server Response
        # 根据文档：当 flags=0b0100 时，仍然包含 Event/SessionId/PayloadLen。
        # 不能直接把 cursor 之后全部当作音频，否则会把协议字段拼进音频数据。
        if cursor + 4 > len(message):
            return -1, "", b""

        event = struct.unpack(">i", message[cursor:cursor+4])[0]
        cursor += 4

        session_id = ""
        if cursor + 4 <= len(message):
            sid_len = struct.unpack(">I", message[cursor:cursor+4])[0]
            cursor += 4
            if 0 < sid_len <= 256 and cursor + sid_len <= len(message):
                session_id = message[cursor:cursor+sid_len].decode("utf-8", errors="ignore")
                cursor += sid_len

        payload = b""
        if cursor + 4 <= len(message):
            payload_len = struct.unpack(">I", message[cursor:cursor+4])[0]
            cursor += 4
            if cursor + payload_len <= len(message):
                payload = message[cursor:cursor+payload_len]

        return event, session_id, payload

    elif msg_type == 12 or msg_type == 15:
        # 【错误响应】Error Server Response
        err_code = struct.unpack(">i", message[cursor:cursor+4])[0]
        cursor += 4
        err_len = struct.unpack(">I", message[cursor:cursor+4])[0]
        cursor += 4
        err_msg = message[cursor:cursor+err_len].decode("utf-8", errors="ignore")
        raise RuntimeError(f"火山 TTS 服务端返回错误: code={err_code}, msg={err_msg}")

    elif msg_type == 9:
        # 【全量事件响应】Full Server Response
        if cursor + 4 > len(message):
            return -1, "", b""

        # 读取 4 字节 Event ID
        event = struct.unpack(">i", message[cursor:cursor+4])[0]
        cursor += 4

        # 读取 Session ID
        session_id = ""
        if cursor + 4 <= len(message):
            sid_len = struct.unpack(">I", message[cursor:cursor+4])[0]
            cursor += 4
            if 0 < sid_len <= 256 and cursor + sid_len <= len(message):
                session_id = message[cursor:cursor+sid_len].decode("utf-8", errors="ignore")
                cursor += sid_len

        # 读取 Payload
        payload = b""
        if cursor + 4 <= len(message):
            payload_len = struct.unpack(">I", message[cursor:cursor+4])[0]
            cursor += 4
            if cursor + payload_len <= len(message):
                payload = message[cursor:cursor+payload_len]

        return event, session_id, payload

    else:
        # 未知 MsgType 直接抛弃
        return -1, "", b""
# def _recv_frame(ws) -> tuple:
#     """
#     接收并解析一帧服务端消息。
#     服务端帧结构（含 WithEvent 标志）：
#       [4B Header] [4B Event] [4B SessionIdLen] [SessionId] [4B PayloadLen] [Payload]
#     返回: (event_id: int, session_id: str, payload: bytes)
#     """
#     message = ws.recv()
#     if isinstance(message, str):
#         message = message.encode("utf-8")
#     if not message or len(message) < 8:
#         raise RuntimeError(f"TTS 服务端返回帧过短: {len(message) if message else 0} bytes")
#
#     # Byte 0: 协议头（忽略，已固定）
#     # Byte 1: 消息类型标志
#     # Byte 2: 序列化方式
#     # Byte 3: 保留
#     header_flags = message[1]  # 用于判断是否含 Event 和 SessionId
#
#     event = struct.unpack(">i", message[4:8])[0]
#     cursor = 8
#
#     # 解析 Session ID
#     session_id = ""
#     if cursor + 4 <= len(message):
#         sid_len = struct.unpack(">I", message[cursor:cursor + 4])[0]
#         cursor += 4
#         # 防御超大 sid_len（可能是 payload length 本身）
#         if 0 < sid_len <= 256 and cursor + sid_len <= len(message):
#             session_id = message[cursor:cursor + sid_len].decode("utf-8", errors="ignore")
#             cursor += sid_len
#
#     # 解析 Payload
#     payload = b""
#     if cursor + 4 <= len(message):
#         payload_len = struct.unpack(">I", message[cursor:cursor + 4])[0]
#         cursor += 4
#         if payload_len < 0 or payload_len > 50 * 1024 * 1024:
#             raise RuntimeError(f"TTS payload 长度异常: {payload_len}")
#         if cursor + payload_len > len(message):
#             raise RuntimeError("TTS payload 被截断")
#         payload = message[cursor:cursor + payload_len]
#
#     return event, session_id, payload


def _wait_for_event(ws, expected_event: int, timeout_frames: int = 200):
    """阻塞等待直到收到期望的服务端事件（最多 timeout_frames 帧，适配慢速网络）。"""
    for i in range(timeout_frames):
        try:
            event, _, _ = _recv_frame(ws)
            if event == expected_event:
                return
            # 其他事件（如 350/351）静默忽略，继续等待
        except Exception as e:
            if i == timeout_frames - 1:
                raise TimeoutError(f"等待事件 {expected_event} 超时（已接收 {timeout_frames} 帧）")
    raise TimeoutError(f"等待事件 {expected_event} 超时（已接收 {timeout_frames} 帧）")


# ──────────────────────────────────────────────
# TTSService 主类
# ──────────────────────────────────────────────
class TTSService:
    """
    对外暴露：synthesize_bytes(text, voice=None, fmt='mp3') -> bytes

    当 USE_VOLC=1 时调用豆包 TTS V3 WebSocket；
    失败时降级到本地 pyttsx3（仅支持 wav 格式）。
    """

    _engine = None
    _engine_lock = threading.Lock()
    _volc_config_invalid_until = 0.0
    _volc_last_config_error = ''

    @classmethod
    def get_default_speaker(cls) -> str:
        return VOLC_TTS_SPEAKER

    @staticmethod
    def _is_supported_volc_speaker(speaker: str) -> bool:
        speaker = (speaker or '').strip()
        return bool(speaker) and (speaker in KNOWN_VOLC_SPEAKERS or speaker.startswith('saturn_'))

    @staticmethod
    def _is_supported_legacy_speaker(speaker: str) -> bool:
        speaker = (speaker or '').strip()
        return bool(speaker) and bool(re.fullmatch(r'BV\d+_streaming', speaker))

    @classmethod
    def _get_legacy_speaker_candidates(cls, voice=None):
        candidates = []

        def add_candidate(value):
            speaker = (value or '').strip()
            if speaker and speaker not in candidates:
                candidates.append(speaker)

        if cls._is_supported_legacy_speaker(voice):
            add_candidate(voice)

        add_candidate(VOLC_TTS_LEGACY_SPEAKER)
        add_candidate('BV001_streaming')
        add_candidate('BV120_streaming')
        return candidates

    @classmethod
    def _get_volc_speaker_candidates(cls, voice=None):
        """返回按优先级排序的火山 speaker 候选列表。"""
        candidates = []

        def add_candidate(value):
            speaker = (value or '').strip()
            if speaker and speaker not in candidates:
                candidates.append(speaker)

        if cls._is_supported_volc_speaker(voice):
            add_candidate(voice)

        add_candidate(cls._resolve_volc_speaker(voice))
        add_candidate(VOLC_TTS_SPEAKER)

        for speaker in DEFAULT_VOLC_2_SPEAKER_CANDIDATES:
            add_candidate(speaker)

        return candidates

    @classmethod
    def _get_volc_attempt_plan(cls, voice=None):
        """构建(resource_id, speaker)组合的重试计划，避免只在单一资源上盲试音色。"""
        attempts = []
        resource_candidates = []

        for resource_id in VOLC_RESOURCE_CANDIDATES:
            rid = (resource_id or '').strip()
            if rid and rid not in resource_candidates:
                resource_candidates.append(rid)

        tts2_speakers = cls._get_volc_speaker_candidates(voice)
        legacy_speakers = cls._get_legacy_speaker_candidates(voice)

        for rid in resource_candidates:
            if rid in ('seed-tts-2.0',):
                for speaker in tts2_speakers:
                    attempts.append((rid, speaker))
                continue

            if rid in ('seed-tts-1.0', 'volc.service_type.10029'):
                for speaker in legacy_speakers:
                    attempts.append((rid, speaker))
                continue

            # 对未知自定义资源，优先尝试 2.0 speaker，再尝试 legacy speaker。
            for speaker in tts2_speakers + legacy_speakers:
                attempts.append((rid, speaker))

        # 去重，保持顺序
        deduped = []
        for item in attempts:
            if item not in deduped:
                deduped.append(item)
        return deduped

    @classmethod
    def _resolve_volc_speaker(cls, voice=None) -> str:
        speaker = (voice or '').strip()
        if not speaker:
            return VOLC_TTS_SPEAKER

        if speaker in LEGACY_VOICE_ALIAS_MAP:
            return LEGACY_VOICE_ALIAS_MAP[speaker]

        # 旧项目中常见的 streaming 命名不是火山官方 speaker，直接回落到当前默认官方音色。
        if re.fullmatch(r'BV\d+_streaming', speaker):
            return VOLC_TTS_SPEAKER

        # 对不在官方 2.0 兼容列表中的值做兜底，避免把明显不兼容的 speaker 直接发给服务端。
        if speaker not in KNOWN_VOLC_SPEAKERS and not speaker.startswith('saturn_'):
            return VOLC_TTS_SPEAKER

        return speaker

    @classmethod
    def _is_volc_voice_config_error(cls, exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            'resource id is mismatched with speaker related resource' in message
            or 'speaker related resource' in message
            or 'invalid speaker' in message
            or 'requested resource not granted' in message
            or 'resource not granted' in message
        )

    @classmethod
    def _is_volc_resource_not_granted_error(cls, exc: Exception) -> bool:
        message = str(exc).lower()
        return 'requested resource not granted' in message or 'resource not granted' in message

    @staticmethod
    def _count_speakable_chars(text: str) -> int:
        return len(_SPEAKABLE_TEXT_PATTERN.findall(text or ''))

    @classmethod
    def _is_non_speech_text(cls, text: str) -> bool:
        return cls._count_speakable_chars(text) == 0

    @classmethod
    def _should_stop_retry_on_empty_audio(cls, text: str) -> bool:
        # 过短文本（如“。\n”“嗯”）在服务端常返回 0 音频帧，继续轮询候选只会放大延迟。
        return cls._count_speakable_chars(text) <= 2

    @classmethod
    def _ensure_engine(cls):
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 is required for local TTS fallback. "
                               "Install with `pip install pyttsx3`")
        if cls._engine is None:
            with cls._engine_lock:
                if cls._engine is None:
                    cls._engine = pyttsx3.init()
        return cls._engine

    @classmethod
    def synthesize_bytes(cls, text: str, voice=None, fmt: str = 'mp3') -> bytes:
        """
        合成文本到音频字节。
        - fmt 强制使用 mp3 或 pcm（流式场景不能用 wav）。
        - USE_VOLC=1 时优先调用豆包 TTS，失败则降级本地。
        """
        text = (text or '').strip()
        if not text:
            return b""

        if cls._is_non_speech_text(text):
            print("[TTSService] 文本不包含可发音字符，跳过 TTS 合成。")
            return None

        # 强制修正：流式场景禁用 wav，统一用 mp3
        safe_fmt = (fmt or 'mp3').lower()
        if safe_fmt == 'wav':
            safe_fmt = 'mp3'
        if safe_fmt not in ('mp3', 'pcm', 'ogg_opus'):
            safe_fmt = 'mp3'

        if USE_VOLC:
            now_ts = time.time()
            if now_ts < cls._volc_config_invalid_until and not VOLC_STRICT_MODE:
                remain = int(cls._volc_config_invalid_until - now_ts)
                print(
                    f"[TTSService] 火山 TTS 暂时跳过（冷却 {remain}s）：{cls._volc_last_config_error}"
                )
                return cls._synthesize_local(text, voice, 'wav')

            attempt_plan = cls._get_volc_attempt_plan(voice)
            last_config_error = None
            denied_resource_ids = set()

            for index, (resource_id, speaker) in enumerate(attempt_plan, start=1):
                if resource_id in denied_resource_ids:
                    continue
                try:
                    if voice and voice.strip() != speaker and index == 1:
                        print(f"[TTSService] speaker 已映射：{voice.strip()} -> {speaker}")
                    print(
                        f"[TTSService] 尝试使用火山 TTS：resource_id={resource_id}，"
                        f"speaker={speaker}（候选 {index}/{len(attempt_plan)}）"
                    )
                    data = cls._synthesize_volc(text, speaker, safe_fmt, resource_id=resource_id)
                    if data:
                        print(
                            f"[TTSService] 火山 TTS 合成成功：resource_id={resource_id}，"
                            f"speaker={speaker}，音频大小={len(data)} bytes"
                        )
                        return data

                    if cls._should_stop_retry_on_empty_audio(text):
                        print(
                            f"[TTSService] 短文本未返回音频（有效字符={cls._count_speakable_chars(text)}），"
                            "停止候选轮询。"
                        )
                        return None

                    print(
                        f"[TTSService] 火山 TTS 未返回音频数据，继续下一个候选："
                        f"resource_id={resource_id}，speaker={speaker}"
                    )
                except Exception as e:
                    if cls._is_volc_voice_config_error(e):
                        last_config_error = e
                        if cls._is_volc_resource_not_granted_error(e):
                            denied_resource_ids.add(resource_id)
                            print(
                                f"[TTSService] 当前账号未开通 resource_id={resource_id}，"
                                "跳过该资源的后续 speaker 重试。"
                            )
                        print(f"[TTSService] 火山 TTS 音色/资源不匹配，尝试下一个候选：{e}")
                        continue

                    if VOLC_STRICT_MODE:
                        print(
                            f"[TTSService] Volc TTS 失败（code={getattr(e, 'code', 'N/A')}），"
                            f"严格模式开启，不降级本地: {e}"
                        )
                        raise

                    print(f"[TTSService] Volc TTS 失败（code={getattr(e, 'code', 'N/A')}），降级至本地 pyttsx3: {e}")
                    break

            if last_config_error is not None:
                cls._volc_last_config_error = str(last_config_error)
                cls._volc_config_invalid_until = time.time() + max(30, VOLC_RETRY_COOLDOWN_SECONDS)
                print(
                    "[TTSService] 所有 resource_id/speaker 组合均失败。"
                    "请检查火山控制台是否已为当前 AppID 开通对应 TTS 资源。"
                )

                if VOLC_STRICT_MODE:
                    raise last_config_error

                print("[TTSService] 已自动降级到本地 TTS，等待冷却期后再重试火山。")
                return cls._synthesize_local(text, voice, 'wav')

            if VOLC_STRICT_MODE:
                print("[TTSService] 严格模式开启：未获取到火山音频，不降级本地。")
                return None

        # 本地降级：pyttsx3 仅支持 wav
        return cls._synthesize_local(text, voice, 'wav')

    @classmethod
    def _synthesize_local(cls, text: str, voice, fmt: str = 'wav') -> bytes:
        """本地 pyttsx3 离线合成（返回 WAV 字节）。"""
        print(f"[TTSService] 启动本地 pyttsx3 合成，文本长度={len(text)}")
        engine = cls._ensure_engine()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + fmt) as tmp:
            tmp_path = tmp.name
        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            with open(tmp_path, 'rb') as f:
                data = f.read()
                print(f"[TTSService] pyttsx3 合成完成，音频大小={len(data)} bytes")
                return data
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    @classmethod
    def _synthesize_volc(cls, text: str, voice=None, fmt: str = 'mp3', resource_id: str = None) -> bytes:
        """
        调用豆包 TTS V3 双向流式 WebSocket API。

        严格遵循状态机：
          StartConnection(1) → wait ConnectionStarted(50)
          StartSession(100)  → wait SessionStarted(150)   [仅传参数，不传文本]
          TaskRequest(200)   → [wait TTSResponse(352)...]
          FinishSession(102) → wait SessionFinished(152)
          FinishConnection(2)
        """
        if websocket is None:
            raise RuntimeError("websocket-client 未安装，请执行: pip install websocket-client")
        if not VOLC_APP_ID:
            raise RuntimeError("VOLC_APP_ID 未配置")
        if not VOLC_ACCESS_TOKEN:
            raise RuntimeError("VOLC_ACCESS_TOKEN 未配置")

        target_voice = (voice or '').strip()
        if not target_voice:
            target_voice = cls._resolve_volc_speaker(voice)
        target_resource_id = (resource_id or VOLC_RESOURCE_ID).strip()
        if not target_resource_id:
            target_resource_id = VOLC_RESOURCE_ID

        target_fmt = (fmt or 'mp3').lower()
        if target_fmt == 'wav':
            target_fmt = 'mp3'
        if target_fmt not in ('mp3', 'pcm', 'ogg_opus'):
            target_fmt = 'mp3'

        # ❌ 错误3修正：每次新建连接必须重新生成 UUID，严禁复用
        connect_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        request_id = uuid.uuid4().hex[:8]

        ws = None
        audio_parts = []
        try:
            # ── 1. 建立 WebSocket 连接（鉴权在 HTTP Upgrade 阶段）──
            ws = websocket.create_connection(
                VOLC_TTS_WS_URL,
                timeout=45,  # 增加 WebSocket 连接超时到 45 秒（Volc 服务可能较慢）
                header=[
                    f"X-Api-App-Key: {VOLC_APP_ID}",
                    f"X-Api-Access-Key: {VOLC_ACCESS_TOKEN}",
                    f"X-Api-Resource-Id: {target_resource_id}",
                    f"X-Api-Connect-Id: {connect_id}",
                    "X-Control-Require-Usage-Tokens-Return: text_words",
                ],
            )
            print(
                f"[TTSService][req={request_id}] WebSocket 已连接，"
                f"connect_id={connect_id}，session_id={session_id}，"
                f"resource_id={target_resource_id}，speaker={target_voice}"
            )

            # ── 2. StartConnection (Event 1) ──
            # 连接事件不携带 Session ID
            ws.send_binary(_pack_connection_frame(
                _EVENT_START_CONNECTION,
                {"event": _EVENT_START_CONNECTION}
            ))
            _wait_for_event(ws, _EVENT_CONNECTION_STARTED)
            print(f"[TTSService][req={request_id}] ConnectionStarted(50) 收到")

            # ── 3. StartSession (Event 100) ──
            session_meta = {
                "user": {
                    "uid": connect_id,
                },
                "event": _EVENT_START_SESSION,
                "namespace": "BidirectionalTTS",
                "req_params": {
                    "speaker": target_voice,
                    "audio_params": {
                        "format": target_fmt,
                        "sample_rate": 24000,
                    },
                    # 官方协议要求 additions 为 jsonstring，而不是 JSON object。
                    "additions": json.dumps({
                        "enable_language_detector": True
                    }, ensure_ascii=False),
                }
            }
            ws.send_binary(_pack_session_frame(
                _EVENT_START_SESSION,
                session_id,
                session_meta
            ))
            _wait_for_event(ws, _EVENT_SESSION_STARTED)
            print(f"[TTSService][req={request_id}] SessionStarted(150) 收到，session_id={session_id}")

            # ── 4. TaskRequest (Event 200) ── 发送合成文本
            task_payload = {
                "user": {
                    "uid": connect_id,
                },
                "event": _EVENT_TASK_REQUEST,
                "namespace": "BidirectionalTTS",
                "req_params": {
                    "text": text,
                },
            }
            ws.send_binary(_pack_session_frame(
                _EVENT_TASK_REQUEST,
                session_id,
                task_payload
            ))
            print(
                f"[TTSService][req={request_id}] TaskRequest(200) 已发送，"
                f"session_id={session_id}，文本长度={len(text)}"
            )

            # ── 5. FinishSession (Event 102) ── 通知服务端文本输入完毕
            ws.send_binary(_pack_session_frame(
                _EVENT_FINISH_SESSION,
                session_id,
                {"event": _EVENT_FINISH_SESSION}
            ))
            print(
                f"[TTSService][req={request_id}] FinishSession(102) 已发送，"
                f"session_id={session_id}，等待音频流..."
            )

            # ── 6. 接收音频流，直到 SessionFinished(152) ──
            # ❌ 错误5修正：必须等到 SessionFinished 再结束
            received_frames = 0
            total_audio_bytes = 0
            while True:
                event, event_session_id, payload = _recv_frame(ws)

                # 防串流：如果收到其他 session 的事件，直接忽略，避免误计数。
                if event_session_id and event_session_id != session_id:
                    if event in (_EVENT_TTS_RESPONSE, _EVENT_SESSION_FINISHED):
                        print(
                            f"[TTSService][req={request_id}] 忽略跨会话事件："
                            f"event={event}，event_session_id={event_session_id}，"
                            f"current_session_id={session_id}"
                        )
                    continue

                if event == _EVENT_TTS_RESPONSE:
                    if payload:
                        audio_parts.append(payload)
                        received_frames += 1
                        total_audio_bytes += len(payload)
                elif event == _EVENT_SESSION_FINISHED:
                    usage_text_words = None
                    if payload:
                        try:
                            finish_payload = json.loads(payload.decode('utf-8', errors='ignore'))
                            usage_text_words = (
                                finish_payload.get('res_params', {}).get('usage', {}).get('text_words')
                                or finish_payload.get('usage', {}).get('text_words')
                                or finish_payload.get('text_words')
                            )
                        except Exception:
                            usage_text_words = None

                    avg_frame_bytes = int(total_audio_bytes / received_frames) if received_frames else 0
                    print(
                        f"[TTSService][req={request_id}] SessionFinished(152) 收到，"
                        f"session_id={session_id}，文本长度={len(text)}，"
                        f"音频帧数={received_frames}，总字节={total_audio_bytes}，"
                        f"平均每帧={avg_frame_bytes} bytes，"
                        f"text_words={usage_text_words if usage_text_words is not None else 'N/A'}"
                    )
                    break
                elif event in (_EVENT_TTS_SENTENCE_START, _EVENT_TTS_SENTENCE_END):
                    # 句子级别时间戳事件，忽略
                    pass
                else:
                    print(
                        f"[TTSService][req={request_id}] 收到未知事件: {event}，"
                        f"session_id={event_session_id or session_id}，忽略"
                    )

            if received_frames == 0:
                print(
                    f"[TTSService][req={request_id}] 当前会话未返回任何音频帧，"
                    f"session_id={session_id}，文本长度={len(text)}"
                )

            # ── 7. FinishConnection (Event 2) ──
            ws.send_binary(_pack_connection_frame(
                _EVENT_FINISH_CONNECTION,
                {"event": _EVENT_FINISH_CONNECTION}
            ))

            return b"".join(audio_parts) if audio_parts else None

        except Exception as e:
            print(f"[TTSService][req={request_id}] _synthesize_volc 异常: {type(e).__name__}: {e}")
            raise
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────
def bytes_to_b64(data_bytes: bytes) -> str:
    """将音频字节编码为 base64 字符串（供 SSE/JSON 传输）。"""
    return base64.b64encode(data_bytes).decode('ascii')
