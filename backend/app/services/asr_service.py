# backend/app/services/asr_service.py
from faster_whisper import WhisperModel
import os
import tempfile

# 延迟加载模型（首次调用时加载）
_model = None
global_speed_cache = {}

def get_whisper_model():
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model

class ASRService:
    @staticmethod
    def transcribe_audio(audio_file):
        model = get_whisper_model()
        # 将传入的 FileStorage 对象保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name

        try:
            # 执行转录
            # 修改后：加入 initial_prompt 强制输出简体中文
            segments, info = model.transcribe(
                temp_path,
                language="zh",
                initial_prompt="以下是一段简体中文的对话。"
            )
            text = "".join([segment.text for segment in segments]).strip()

            # ================= 计算语速并悄悄存入缓存 =================
            duration = info.duration  # 音频总时长
            char_count = len(text)  # 纯文本字数

            if text and duration > 0:
                speech_speed = round(char_count / duration, 2)
                # 以“识别出的文本”本身作为 Key，悄悄存下语速
                global_speed_cache[text] = speech_speed
            # ==========================================================

            # 只返回最干净的纯文本！前端什么脏数据都看不到
            return text

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)