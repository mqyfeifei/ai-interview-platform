from flask import current_app
from app.extensions import socketio
from threading import Lock, Thread
import time
import base64
import io
import wave
import json

# 本模块实现 WebSocket 的 ASR 接口（实时流式识别版）
# 客户端通过发送 'audio_chunk' 事件来上传分片：
# data = { 'voice_id': str, 'seq': int, 'chunk_b64': str, 'is_end': 0/1 }
# 服务器会在识别到 partial 时发送 'asr_partial' 事件：{ 'voice_id': str, 'seq': int, 'text': str }
# 服务器在最终完成后发送 'asr_final' 事件：{ 'voice_id': str, 'text': str }

thread_lock = Lock()
# per-voice buffers and state
_voice_states = {}
# Structure: _voice_states[voice_id] = {
#   'buffer': bytearray(), 'chunks': [], 'last_update': timestamp, 'last_emit': timestamp, 
#   'transcribing': False, 'realtime_service': RealtimeASRService instance
# }

DEBOUNCE_SECONDS = 0.6  # time to wait before running intermediate transcription


def _ensure_voice_state(voice_id):
    with thread_lock:
        if voice_id not in _voice_states:
            _voice_states[voice_id] = {
                'buffer': bytearray(),
                'chunks': [],  # 新增：累积音频分片
                'last_update': time.time(),
                'last_emit': 0,
                'transcribing': False,
                'realtime_service': None  # 实时ASR服务实例
            }
        return _voice_states[voice_id]


def _cleanup_voice_state(voice_id):
    with thread_lock:
        if voice_id in _voice_states:
            del _voice_states[voice_id]


def _build_wav_bytes(pcm_bytes, rate=16000, channels=1, sampwidth=2):
    # pcm_bytes are raw frames; write a WAV header around them
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)
    return bio.getvalue()


def _transcription_worker(voice_id, is_final=False):
    """Background worker: convert current buffer to WAV and transcribe with fallback."""
    state = _voice_states.get(voice_id)
    if not state:
        return
    # mark transcribing
    state['transcribing'] = True
    try:
        pcm = bytes(state['buffer'])
        if not pcm:
            return
        wav_bytes = _build_wav_bytes(pcm)
        # call fallback recognizer (tries Tencent SentenceRecognition then Whisper)
        from app.services.asr_service import _recognize_with_fallback
        start = time.time()
        text = _recognize_with_fallback(wav_bytes)
        elapsed = int((time.time() - start) * 1000)
        if text:
            if is_final:
                socketio.emit('asr_final', {'voice_id': voice_id, 'text': text, 'elapsed_ms': elapsed})
            else:
                socketio.emit('asr_partial', {'voice_id': voice_id, 'text': text, 'elapsed_ms': elapsed})
                state['last_emit'] = time.time()
    except Exception as e:
        print(f"[WS] 转写后台任务异常: {e}")
        socketio.emit('asr_error', {'error': str(e)})
    finally:
        state['transcribing'] = False
        if is_final:
            # cleanup buffer
            _cleanup_voice_state(voice_id)


def register_asr_handlers(sio):
    # handlers are registered on import
    pass


@socketio.on('connect')
def handle_connect():
    print('[WS] 客户端连接')


@socketio.on('disconnect')
def handle_disconnect():
    print('[WS] 客户端断开')


@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """
    data: dict with keys: voice_id, seq, chunk_b64, is_end
    chunk_b64 may be empty string for final packet with is_end=1
    """
    try:
        voice_id = data.get('voice_id') or str(int(time.time() * 1000))
        seq = data.get('seq', 0)
        chunk_b64 = data.get('chunk_b64')
        is_end = int(data.get('is_end', 0))
        
        print(f"[WS] 收到音频分片: voice_id={voice_id}, seq={seq}, is_end={is_end}, chunk_size={len(chunk_b64) if chunk_b64 else 0}")

        state = _ensure_voice_state(voice_id)

        # ==================== 使用腾讯云实时流式识别 ====================
        if chunk_b64:
            # 初始化实时ASR服务（如果还没有）
            if state['realtime_service'] is None:
                from app.services.realtime_asr_service import get_realtime_asr_service
                from flask import current_app
                
                secret_id = current_app.config.get('TENCENT_SECRET_ID', '')
                secret_key = current_app.config.get('TENCENT_SECRET_KEY', '')
                appid = current_app.config.get('TENCENT_ASR_APP_ID', '')
                
                print(f"[WS] 配置检查: SecretId={secret_id[:20] if secret_id else 'None'}..., SecretKey长度={len(secret_key) if secret_key else 0}, AppID={appid}")
                
                if not secret_id or not secret_key or not appid:
                    print("[WS] 错误: 腾讯云密钥未配置")
                    socketio.emit('asr_error', {'error': '腾讯云密钥未配置'})
                    return
                
                # 创建实时ASR服务
                realtime_service = get_realtime_asr_service(secret_id, secret_key, appid)
                state['realtime_service'] = realtime_service
                
                # 定义回调函数
                def on_asr_result(text, is_final):
                    print(f"[WS] ASR回调: text='{text[:50] if text else ''}...', is_final={is_final}")
                    if text:
                        if is_final:
                            socketio.emit('asr_final', {
                                'voice_id': voice_id,
                                'text': text
                            })
                            print(f"[WS] ✓ 已发送最终结果")
                        else:
                            socketio.emit('asr_partial', {
                                'voice_id': voice_id,
                                'seq': seq,
                                'text': text
                            })
                            print(f"[WS] ✓ 已发送中间结果")
                
                # 启动实时识别
                realtime_service.start(on_asr_result)
                print(f"[WS] ✓ 实时ASR服务已启动: {voice_id}")
            
            # 解码音频数据
            chunk_bytes = base64.b64decode(chunk_b64)
            
            # 发送音频到实时ASR服务
            if state['realtime_service']:
                state['realtime_service'].send_audio(
                    audio_bytes=chunk_bytes,
                    seq=seq,
                    is_end=(is_end == 1)
                )
                print(f"[WS] ✓ 已发送音频分片 (seq={seq}, size={len(chunk_bytes)} bytes)")
        
        # ✅ 关键修复：如果是结束标记，延迟清理以等待最终结果
        if is_end:
            print(f"[WS] 收到结束标记")
            
            # ✅ 不要立即停止服务，而是发送结束指令后等待最终结果
            if state['realtime_service']:
                # 发送结束指令（让腾讯云返回最终结果）
                if state['realtime_service'].ws:
                    try:
                        end_msg = {"type": "end"}
                        state['realtime_service'].ws.send(json.dumps(end_msg))
                        print(f"[WS] ✓ 已发送结束指令，等待最终结果...")
                    except Exception as e:
                        print(f"[WS] ✗ 发送结束指令失败: {e}")
                
                # ✅ 延迟清理状态（给腾讯云时间返回最终结果）
                import threading
                def delayed_cleanup():
                    time.sleep(3)  # 等待3秒让腾讯云返回最终结果
                    if state['realtime_service']:
                        state['realtime_service'].stop()
                        state['realtime_service'] = None
                    _cleanup_voice_state(voice_id)
                    print(f"[WS] ✓ 已清理语音状态")
                
                cleanup_thread = threading.Thread(target=delayed_cleanup)
                cleanup_thread.daemon = True
                cleanup_thread.start()
            else:
                # 如果没有实时服务，直接清理
                _cleanup_voice_state(voice_id)
        # ================================================================

    except Exception as e:
        print(f"[WS] ✗ 处理音频分片异常: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('asr_error', {'error': str(e)})
