# backend/app/services/asr_service.py
from faster_whisper import WhisperModel
import os
import tempfile

# 延迟加载模型（首次调用时加载）
_model = None

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
            segments, info = model.transcribe(temp_path, language="zh")
            text = "".join([segment.text for segment in segments])
            return text
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)