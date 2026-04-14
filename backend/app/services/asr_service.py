# backend/app/services/asr_service.py
"""
语音识别服务(ASR)
支持本地Whisper模型和云端API(阿里云/腾讯云)
通过环境变量切换服务商
"""

import os
import tempfile
import requests
import base64
import time

# avoid linter warnings for unused crypto libs (they're not needed here)
# removed unused: hmac, hashlib, json

# 尝试导入 pydub 用于音频格式转换
AudioSegment = None
try:
    from pydub import AudioSegment as _AudioSegment
    AudioSegment = _AudioSegment

    # 设置 ffmpeg 和 ffprobe 的路径
    FFMPEG_PATH = r"C:\Users\32307\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
    
    AudioSegment.converter = f"{FFMPEG_PATH}\\ffmpeg.exe"
    AudioSegment.ffprobe = f"{FFMPEG_PATH}\\ffprobe.exe"
    
    HAS_PYDUB = True
    print(f"[ASR] pydub 初始化成功")
    print(f"[ASR]   ffmpeg: {AudioSegment.converter}")
    print(f"[ASR]   ffprobe: {AudioSegment.ffprobe}")
except ImportError:
    HAS_PYDUB = False
    print("[警告] pydub 未安装，音频格式转换功能不可用。请运行: pip install pydub")

# ==================== 配置区域 ====================
# 当前使用的ASR服务商: 'local'(本地Whisper), 'aliyun', 'tencent'
# 默认改为 tencent 实时流式识别，若需改回本地或阿里云请设置环境变量 ASR_PROVIDER
ASR_PROVIDER = os.getenv('ASR_PROVIDER', 'tencent')

# 阿里云配置
ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
ALIYUN_APP_KEY = os.getenv('ALIYUN_ASR_APP_KEY', '')

# 腾讯云配置
TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', '')
TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', '')
TENCENT_APP_ID = os.getenv('TENCENT_ASR_APP_ID', '')
# ==================================================

# 全局语速缓存(用于情感分析)
global_speed_cache = {}

# 延迟加载本地模型（首次调用时加载）
_local_model = None

def get_whisper_model():
    """获取本地Whisper模型(单例模式)"""
    global _local_model
    if _local_model is None:
        from faster_whisper import WhisperModel
        _local_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _local_model


class ASRService:
    """
    语音识别服务类
    
    使用示例:
        text = ASRService.transcribe_audio(audio_file)
        print(text)
    """
    
    @staticmethod
    def _convert_to_tencent_format(input_path):
        """
        将音频转换为腾讯云ASR要求的格式:
        - WAV格式
        - 16kHz采样率
        - 单声道
        - 16bit位深
        
        Args:
            input_path: 输入音频文件路径
            
        Returns:
            str: 转换后的临时文件路径
        """
        import subprocess
        
        # ffmpeg 路径
        FFMPEG_EXE = r"C:\Users\32307\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
        
        if not os.path.exists(FFMPEG_EXE):
            print(f"[ASR] ffmpeg 不存在: {FFMPEG_EXE}，跳过格式转换")
            return input_path
        
        output_path = input_path + '_converted.wav'
        
        try:
            print(f"[ASR] 开始音频格式转换: {input_path}")
            
            # 使用 ffmpeg 命令行转换
            cmd = [
                FFMPEG_EXE,
                '-i', input_path,          # 输入文件
                '-ac', '1',                 # 单声道
                '-ar', '16000',             # 16kHz 采样率
                '-sample_fmt', 's16',       # 16bit 位深
                '-y',                       # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"[ASR] 音频格式转换成功: {file_size} bytes")
                return output_path
            else:
                print(f"[ASR] ffmpeg 转换失败: {result.stderr}")
                return input_path
        
        except Exception as e:
            print(f"[ASR] 音频格式转换异常: {str(e)}，使用原始文件")
            import traceback
            traceback.print_exc()
            return input_path
    
    @staticmethod
    def transcribe_audio(audio_file):
        """
        转录音频文件为文本
        
        Args:
            audio_file: Flask FileStorage对象或文件路径
            
        Returns:
            str: 识别出的文本
        """
        # Force Tencent real-time streaming for all ASR calls to avoid long-batch recordings.
        # If you need to revert to other providers, set ASR_PROVIDER explicitly and change here.
        print("[ASR] 强制使用腾讯云实时流式识别（SimultaneousInterpreting）")
        return ASRService._transcribe_with_tencent(audio_file)

    @staticmethod
    def _transcribe_with_whisper(audio_file):
        """
        使用本地Whisper模型进行语音识别
        
        Args:
            audio_file: Flask FileStorage对象
            
        Returns:
            str: 识别文本
        """
        model = get_whisper_model()
        
        # 将传入的 FileStorage 对象保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name

        try:
            # 执行转录
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
                # 以"识别出的文本"本身作为 Key，悄悄存下语速
                global_speed_cache[text] = speech_speed
            # ==========================================================

            # 只返回最干净的纯文本！前端什么脏数据都看不到
            return text

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def _transcribe_with_aliyun(audio_file):
        """
        使用阿里云智能语音交互API进行识别
        
        API文档: https://help.aliyun.com/document_detail/304159.html
        
        Args:
            audio_file: Flask FileStorage对象
            
        Returns:
            str: 识别文本
        """
        print("[ASR] 使用阿里云语音识别")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
        
        try:
            # 读取音频文件
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # 阿里云一句话识别API
            url = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/FlashRecognizer"
            
            # 构建请求头
            headers = {
                'Content-Type': 'application/octet-stream',
                'X-NLS-Token': ALIYUN_ACCESS_KEY_SECRET,  # 简化版，实际需签名
            }
            
            # 构建请求参数
            params = {
                'appkey': ALIYUN_APP_KEY,
                'format': 'wav',
                'sample_rate': '16000',
                'enable_punctuation_prediction': 'true',
                'enable_inverse_text_normalization': 'true',
            }
            
            # 发送请求
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=audio_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 20000000:
                    text = result.get('result', '').strip()
                    
                    # 计算语速
                    duration = len(audio_data) / (16000 * 2)  # 假设16bit采样
                    char_count = len(text)
                    if text and duration > 0:
                        speech_speed = round(char_count / duration, 2)
                        global_speed_cache[text] = speech_speed
                    
                    return text
                else:
                    print(f"[ASR] 阿里云识别失败: {result}")
                    raise Exception(f"阿里云ASR错误: {result.get('message', '未知错误')}")
            else:
                raise Exception(f"阿里云ASR HTTP错误: {response.status_code}")
        
        except Exception as e:
            print(f"[ASR] 阿里云识别异常: {str(e)}，降级使用本地Whisper")
            # 降级到本地Whisper
            return ASRService._transcribe_with_whisper(audio_file)
        
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def _transcribe_with_tencent(audio_file):
        """
        使用腾讯云语音识别API进行识别（含情感分析）
        
        API文档: https://cloud.tencent.com/document/product/1093/35799
        情感识别参数: EmoticonRecognition=2 开启情绪识别
        
        使用录音文件识别模式（支持最长5小时）
        
        Args:
            audio_file: Flask FileStorage对象
            
        Returns:
            str: 识别文本（可能包含情绪标签如[pause]、[laughter]等）
        """
        print("[ASR] 使用腾讯云语音识别（含情感分析）- 录音文件识别模式")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
        
        converted_path = None
        
        try:
            # ==================== 音频格式转换 ====================
            converted_path = ASRService._convert_to_tencent_format(temp_path)
            # ===================================================
            
            # 读取音频文件并Base64编码
            with open(converted_path, 'rb') as f:
                audio_data = f.read()

            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # 尝试使用腾讯云官方SDK
            # define placeholders to satisfy static analyzer
            credential = None
            ClientProfile = None
            HttpProfile = None
            aai_client = None
            models = None
            try:
                from tencentcloud.common import credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                from tencentcloud.aai.v20180522 import aai_client, models

                print("[ASR] 使用腾讯云官方SDK - 录音文件识别模式")

                # 实例化认证对象
                cred = credential.Credential(
                    TENCENT_SECRET_ID,
                    TENCENT_SECRET_KEY
                )

                # 实例化HTTP选项
                httpProfile = HttpProfile()
                httpProfile.endpoint = "aai.tencentcloudapi.com"

                # 实例化Client选项
                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile

                # 实例化客户端
                client = aai_client.AaiClient(cred, "ap-guangzhou", clientProfile)

                # 使用 CreateRecTask 录音文件识别（支持情感标签）
                create_req = models.CreateRecTaskRequest()
                create_params = {
                    "EngineModelType": "16k_zh",
                    "ChannelNum": 1,
                    "ResTextFormat": 0,
                    "SourceType": 1,
                    "Data": audio_base64,
                    "EmoticonRecognition": 2,  # 开启情感识别
                }
                create_req.from_json_string(json.dumps(create_params))
                
                create_resp = client.CreateRecTask(create_req)
                task_id = create_resp.Data.TaskId
                print(f"[ASR] 创建识别任务成功，TaskId: {task_id}")
                
                # 轮询查询任务状态
                max_retries = 60  # 最多等待120秒
                retry_count = 0
                
                while retry_count < max_retries:
                    time.sleep(2)
                    retry_count += 1
                    
                    status_req = models.DescribeTaskStatusRequest()
                    status_req.TaskId = task_id
                    status_resp = client.DescribeTaskStatus(status_req)
                    
                    status = status_resp.Data.StatusStr
                    
                    if status == "success":
                        text = status_resp.Data.Result.strip()
                        if text:
                            # 计算并缓存语速
                            try:
                                duration = len(audio_data) / (16000 * 2)  # 假设16k采样率
                                char_count = len(text)
                                if char_count and duration > 0:
                                    global_speed_cache[text] = round(char_count / duration, 2)
                            except Exception:
                                pass
                            
                            print(f"[ASR] 录音文件识别完成: {text[:120]}...")
                            return text
                        else:
                            raise Exception("识别结果为空")
                            
                    elif status == "failed":
                        raise Exception(f"腾讯云ASR识别失败: {status_resp.Data.ErrorMsg}")
                    else:
                        print(f"[ASR] 识别进行中... ({retry_count}/{max_retries})")
                        continue
                
                raise Exception("识别超时")

            except ImportError:
                print("[ASR] 未安装腾讯云SDK，使用HTTP API方式")
                raise Exception("请安装腾讯云SDK: pip install tencentcloud-sdk-python")

        except Exception as e:
            print(f"[ASR] 腾讯云识别异常: {str(e)}，降级使用本地Whisper")
            # 降级到本地Whisper
            return ASRService._transcribe_with_whisper(audio_file)
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            # 清理转换后的文件
            if converted_path and converted_path != temp_path and os.path.exists(converted_path):
                os.remove(converted_path)

    @staticmethod
    def _transcribe_bytes_with_whisper(audio_bytes):
        """Helper: write bytes to temp wav and transcribe with local Whisper model."""
        try:
            model = get_whisper_model()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                tmp = f.name
            try:
                segments, info = model.transcribe(tmp, language="zh", initial_prompt="以下是一段简体中文的对话。")
                text = "".join([seg.text for seg in segments]).strip()
                return text
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        except Exception as e:
            print(f"[ASR] 本地Whisper转写失败: {e}")
            return ""

    @staticmethod
    def _recognize_with_fallback(audio_bytes):
        """
        Try Tencent SentenceRecognition on the full audio bytes. If the Tencent SimultaneousInterpreting
        API is unavailable (or SentenceRecognition fails), fall back to local Whisper.
        Returns the recognized text (string).
        """
        # Try Tencent first (synchronous short-audio API)
        try:
            client, models = _init_tencent_client()
            req = models.SentenceRecognitionRequest()
            req.ProjectId = 0
            req.SubServiceType = 2  # 一句话识别
            # For some SDKs the EngSerViceType naming varies; use '16k' or '16k_zh' depending on SDK
            try:
                req.EngSerViceType = '16k'
            except Exception:
                try:
                    req.EngSerViceType = '16k_zh'
                except Exception:
                    pass
            req.SourceType = 1
            # VoiceFormat may expect 'wav' or integer; set what previous code used
            try:
                req.VoiceFormat = 'wav'
            except Exception:
                try:
                    req.VoiceFormat = 1
                except Exception:
                    pass
            req.UsrAudioKey = str(int(time.time() * 1000))
            req.Data = base64.b64encode(audio_bytes).decode('utf-8')
            req.DataLen = len(audio_bytes)

            resp = client.SentenceRecognition(req)
            text = getattr(resp, 'Result', '') or ''
            text = text.strip()
            if text:
                return text
            else:
                raise Exception('SentenceRecognition 返回空')
        except Exception as e:
            # If Tencent fails (including ActionOffline), fallback to Whisper
            print(f"[ASR] SentenceRecognition/腾讯同步识别失败或不可用: {e}，降级使用本地Whisper")
            return ASRService._transcribe_bytes_with_whisper(audio_bytes)

def _init_tencent_client():
    """延迟创建并缓存腾讯 AAI 客户端"""
    # keep client cached on module to avoid repeated auth
    global _tencent_client, _tencent_models
    try:
        if '_tencent_client' in globals() and _tencent_client is not None:
            return _tencent_client, _tencent_models
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.aai.v20180522 import aai_client, models

        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "aai.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = aai_client.AaiClient(cred, "ap-guangzhou", clientProfile)
        _tencent_client = client
        _tencent_models = models
        return _tencent_client, _tencent_models
    except Exception as e:
        print(f"[ASR] 初始化腾讯客户端失败: {e}")
        raise


def _call_tencent_simultaneous_on_chunk(voice_id, seq, chunk_b64, is_end):
    """
    在 WebSocket 场景下，按分片调用腾讯 SimultaneousInterpreting 接口并返回 partial AsrText（如果有）
    """
    client, models = _init_tencent_client()
    try:
        req = models.SimultaneousInterpretingRequest()
        req.ProjectId = 0
        req.SubServiceType = 1
        req.RecEngineModelType = '16k_zh'
        req.Data = chunk_b64
        req.DataLen = len(base64.b64decode(chunk_b64)) if chunk_b64 else 0
        req.VoiceId = voice_id
        req.IsEnd = 1 if is_end else 0
        req.VoiceFormat = 1
        req.Seq = seq
        resp = client.SimultaneousInterpreting(req)
        text = getattr(resp, 'AsrText', '') or ''
        return text.strip()
    except Exception as e:
        print(f"[ASR] 分片识别异常: {e}")
        return ''
