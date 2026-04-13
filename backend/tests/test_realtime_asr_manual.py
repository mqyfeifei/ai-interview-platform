"""
腾讯云实时语音识别测试脚本

使用方法：
1. 确保已安装依赖：pip install websocket-client pyaudio
2. 运行脚本：python tests/test_realtime_asr_manual.py
3. 按 Enter 开始录音，再次按 Enter 停止
4. 观察控制台输出的识别结果
"""

import os
import sys
import time
import threading
import base64
import json
import wave
import struct

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import pyaudio
except ImportError:
    print("❌ 错误: 未安装 pyaudio")
    print("请运行: pip install pyaudio")
    sys.exit(1)

try:
    import websocket
except ImportError:
    print("❌ 错误: 未安装 websocket-client")
    print("请运行: pip install websocket-client")
    sys.exit(1)

from dotenv import load_dotenv

# 加载环境变量 - 修正路径
env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
print(f"[配置] 尝试加载 .env 文件: {env_path}")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[配置] ✓ .env 文件加载成功")
else:
    print(f"[配置] ✗ .env 文件不存在: {env_path}")
    sys.exit(1)


class RealtimeASRTester:
    """实时ASR测试器"""
    
    def __init__(self):
        # 从环境变量读取配置
        self.secret_id = os.getenv('TENCENT_SECRET_ID', '').strip()
        self.secret_key = os.getenv('TENCENT_SECRET_KEY', '').strip()
        self.appid = os.getenv('TENCENT_ASR_APP_ID', '').strip()
        
        if not all([self.secret_id, self.secret_key, self.appid]):
            print("❌ 错误: 腾讯云密钥未配置")
            print("请在 backend/app/.env 文件中配置:")
            print("  TENCENT_SECRET_ID=xxx")
            print("  TENCENT_SECRET_KEY=xxx")
            print("  TENCENT_ASR_APP_ID=xxx")
            sys.exit(1)
        
        print("=" * 60)
        print("腾讯云实时语音识别测试")
        print("=" * 60)
        print(f"✓ SecretId: {self.secret_id[:20]}...")
        print(f"✓ SecretKey: {self.secret_key[:10]}... (长度: {len(self.secret_key)})")
        print(f"✓ AppID: {self.appid}")
        print("=" * 60)
        
        # WebSocket 相关
        self.ws = None
        self.voice_id = None
        self.is_recording = False
        self.seq = 0
        
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024  # 每次读取的帧数
        
        # PyAudio
        self.audio = None
        self.stream = None
        
    def _generate_sign(self, params):
        """
        生成腾讯云 WebSocket 签名
        
        根据官方文档：
        1. 对除 signature 之外的所有参数按字典序排序
        2. 拼接签名原文：asr.cloud.tencent.com/asr/v2/{appid}?{params}
        3. 使用 SecretKey 进行 HMAC-SHA1 加密
        4. Base64 编码
        5. URL 编码
        """
        import hmac
        import hashlib
        import urllib.parse
        
        # 按字典序排序参数
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 生成签名原文（注意：不包含 GET 前缀，包含 appid）
        sign_str = f"asr.cloud.tencent.com/asr/v2/{self.appid}?{query_string}"
        
        print(f"[签名] 签名原文: {sign_str[:150]}...")
        
        # HMAC-SHA1 签名
        sign = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64 编码
        signature = base64.b64encode(sign).decode('utf-8')
        
        # URL 编码（必须！）
        signature_encoded = urllib.parse.quote(signature, safe='')
        
        print(f"[签名] 原始签名: {signature[:50]}...")
        print(f"[签名] URL编码后: {signature_encoded[:50]}...")
        
        return signature_encoded
    
    def _build_ws_url(self):
        """构建 WebSocket URL"""
        import urllib.parse
        import random
        
        timestamp = int(time.time())
        expired = timestamp + 24 * 3600
        nonce = random.randint(100000000, 999999999)  # 随机正整数
        
        print(f"\n[配置] SecretId: {self.secret_id[:20]}...")
        print(f"[配置] SecretKey 长度: {len(self.secret_key)}")
        print(f"[配置] AppID: {self.appid}")
        print(f"[配置] Timestamp: {timestamp}")
        print(f"[配置] Nonce: {nonce}")
        
        params = {
            'secretId': self.secret_id,
            'timestamp': str(timestamp),
            'expired': str(expired),
            'nonce': str(nonce),
            'voice_id': self.voice_id or str(timestamp),
            # 启动指令参数（必须包含在 URL 中）
            'engine_model_type': '16k_zh',
            'voice_format': '1',
            'needvad': '1',
            'emoticon_recognition': '2',
        }
        
        signature = self._generate_sign(params)
        
        # 关键修复：先对签名参数按字典序排序，再添加 signature
        sorted_params = sorted(params.items())
        sorted_params.append(('signature', signature))
        
        # 手动构建查询字符串，确保顺序正确
        query_parts = [f"{k}={v}" for k, v in sorted_params]
        query_string = "&".join(query_parts)
        
        ws_url = f"wss://asr.cloud.tencent.com/asr/v2/{self.appid}?{query_string}"
        
        print(f"\n[URL] {ws_url[:200]}...\n")
        
        return ws_url
    
    def _on_message(self, ws, message):
        """处理 WebSocket 消息"""
        try:
            # 调试：打印所有收到的消息
            msg_type = type(message).__name__
            if isinstance(message, bytes):
                print(f"\n[收到二进制消息] 长度: {len(message)} bytes")
                return  # 忽略二进制消息（可能是回声）
            
            print(f"\n[收到文本消息] {message[:300]}")
            
            data = json.loads(message)
            
            # 检查是否有错误
            if 'code' in data and data['code'] != 0:
                print(f"❌ [错误] Code: {data['code']}, Message: {data.get('message', 'Unknown')}")
                return
            
            # 识别结果
            if 'result' in data:
                result = data['result']
                print(f"[DEBUG] result 字段: {result}")
                
                # 关键修复：字段名是 voice_text_str，不是 text
                text = result.get('voice_text_str', '')
                slice_type = result.get('slice_type', 0)  # 0=中间结果, 2=最终结果
                
                print(f"[DEBUG] text='{text}', slice_type={slice_type}")
                
                if not text:
                    print("[DEBUG] text 为空，跳过")
                    return
                
                # 判断是否是最终结果
                is_final = (slice_type == 2)
                
                if is_final:
                    print(f"\n✅ [最终结果] {text}")
                else:
                    print(f"\r⏳ [中间结果] {text}", end='', flush=True)
            
            # 握手成功确认
            elif data.get('code') == 0 and 'voice_id' in data:
                print(f"✓ 握手成功! voice_id: {data['voice_id']}")
            else:
                print(f"[DEBUG] 未知消息格式: {list(data.keys())}")
                
        except Exception as e:
            print(f"\n❌ [消息处理异常] {e}")
            import traceback
            traceback.print_exc()
    
    def _on_error(self, ws, error):
        """处理 WebSocket 错误"""
        print(f"\n❌ [WebSocket 错误] {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """处理 WebSocket 关闭"""
        print(f"\n[连接关闭] {close_status_code} - {close_msg}")
    
    def _on_open(self, ws):
        """处理 WebSocket 打开"""
        print("[✓] WebSocket 连接成功")
        print("[✓] 握手成功，准备接收音频数据")
        # 注意：v2 接口握手成功后不需要发送 start 命令
    
    def connect(self):
        """连接到腾讯云 ASR"""
        self.voice_id = str(int(time.time() * 1000))
        ws_url = self._build_ws_url()
        
        print(f"\n[→] 正在连接到: {ws_url[:80]}...")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # 在后台线程中运行
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待连接建立
        time.sleep(1)
        
        if self.ws.sock and self.ws.sock.connected:
            print("[✓] 连接成功！\n")
            return True
        else:
            print("[✗] 连接失败！\n")
            return False
    
    def send_audio(self, audio_data):
        """发送音频数据（二进制）"""
        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            return False
        
        try:
            # 关键修复：直接发送二进制音频数据，不要包装成 JSON！
            # 官方文档要求：客户端持续上传 binary message 到后台
            self.ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
            self.seq += 1
            return True
            
        except Exception as e:
            print(f"[✗] 发送音频失败: {e}")
            return False
    
    def stop(self):
        """停止识别"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                # 根据官方文档，发送结束指令
                end_msg = {"type": "end"}
                self.ws.send(json.dumps(end_msg))
                print("\n[→] 已发送结束指令")
            except Exception as e:
                print(f"[✗] 发送结束指令失败: {e}")
        
        if self.ws:
            self.ws.close()
    
    def record_and_send(self):
        """录音并发送"""
        self.audio = pyaudio.PyAudio()
        
        print("\n" + "=" * 60)
        print("🎤 准备就绪！")
        print("=" * 60)
        print("👉 按 Enter 键开始录音")
        input()
        
        print("\n🔴 正在录音... (再次按 Enter 停止)")
        
        # 打开音频流
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        self.is_recording = True
        self.seq = 0
        
        # 在后台线程中录音
        def record_thread():
            while self.is_recording:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.send_audio(data)
                except Exception as e:
                    print(f"[✗] 录音异常: {e}")
                    break
        
        thread = threading.Thread(target=record_thread)
        thread.daemon = True
        thread.start()
        
        # 等待用户输入
        input()
        
        print("\n⏹️  停止录音...")
        self.is_recording = False
        
        # 等待一小段时间让最后的音频发送完
        time.sleep(0.5)
        
        # 停止录音流
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
    
    def run(self):
        """运行测试"""
        try:
            # 1. 连接
            if not self.connect():
                print("\n❌ 连接失败，请检查配置和网络")
                return
            
            # 2. 录音并发送
            self.record_and_send()
            
            # 3. 停止识别
            time.sleep(1)  # 等待识别完成
            self.stop()
            
            print("\n" + "=" * 60)
            print("✅ 测试完成！")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
            self.stop()
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.stop()


if __name__ == '__main__':
    tester = RealtimeASRTester()
    tester.run()
