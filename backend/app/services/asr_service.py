# backend/app/services/asr_service.py
from faster_whisper import WhisperModel
import os
import tempfile

# 预加载模型（建议在应用启动时加载至内存）
model = WhisperModel("small", device="cpu", compute_type="int8")

class ASRService:
    @staticmethod
    def transcribe_audio(audio_file):
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