# backend/app/services/realtime_asr_service.py
"""
腾讯云实时语音流式识别服务
使用 WebSocket 协议实现真正的实时语音转文字 + 情感分析

特性：
- 真正的实时流式识别（延迟 < 500ms）
- 支持情感标签识别
- WebSocket 长连接
- 边说边出文字
"""

import websocket
import json
import base64
import time
import threading
import hmac
import hashlib
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import urlencode


class RealtimeASRService:
    """
    腾讯云实时语音流式识别服务
    
    使用示例:
        service = RealtimeASRService(
            secret_id='xxx',
            secret_key='xxx',
            appid='xxx'
        )
        
        def on_result(text, is_final):
            print(f"识别结果: {text}, 是否结束: {is_final}")
        
        service.start(on_result)
        service.send_audio(audio_bytes)
        service.stop()
    """
    
    def __init__(self, secret_id: str, secret_key: str, appid: str, region: str = "ap-guangzhou"):
        self.secret_id = secret_id.strip()  # 去除首尾空格
        self.secret_key = secret_key.strip()  # 去除首尾空格
        self.appid = str(appid).strip()  # 确保是字符串
        self.region = region
        
        # WebSocket 配置
        self.ws_url = "wss://asr.cloud.tencent.com/asr/v2/"
        self.ws = None
        self.ws_thread = None
        
        # 状态管理
        self.voice_id = None
        self.is_running = False
        self.callback = None
        
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.bits_per_sample = 16
        
    def _generate_sign(self, params: dict, appid: str) -> str:
        """
        生成腾讯云 WebSocket 签名
        
        根据官方文档：
        1. 对除 signature 之外的所有参数按字典序排序
        2. 拼接签名原文：asr.cloud.tencent.com/asr/v2/{appid}?{params}
        3. 使用 SecretKey 进行 HMAC-SHA1 加密
        4. Base64 编码
        5. URL 编码
        
        参考：https://cloud.tencent.com/document/product/1093/48982
        """
        import urllib.parse
        
        # 按字典序排序参数
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 生成签名原文（注意：不包含 GET 前缀，包含 appid）
        sign_str = f"asr.cloud.tencent.com/asr/v2/{appid}?{query_string}"
        
        print(f"[实时ASR] 签名原文: {sign_str[:150]}...")
        
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
        
        print(f"[实时ASR] 原始签名: {signature[:50]}...")
        print(f"[实时ASR] URL编码后: {signature_encoded[:50]}...")
        
        return signature_encoded
    
    def _build_ws_url(self) -> str:
        """构建 WebSocket URL"""
        import random
        
        timestamp = int(time.time())
        expired = timestamp + 24 * 3600  # 24小时有效期
        nonce = random.randint(100000000, 999999999)  # 随机正整数
        
        print(f"[实时ASR] 配置检查:")
        print(f"  - SecretId: {self.secret_id[:20]}...")
        print(f"  - SecretKey 长度: {len(self.secret_key)}")
        print(f"  - AppID: {self.appid}")
        print(f"  - Timestamp: {timestamp}")
        print(f"  - Expired: {expired}")
        print(f"  - Nonce: {nonce}")
        
        # 关键修复：根据官方文档，启动指令的参数也要放在 URL 中并参与签名！
        params = {
            'secretId': self.secret_id,
            'timestamp': str(timestamp),
            'expired': str(expired),
            'nonce': str(nonce),
            'voice_id': self.voice_id or str(timestamp),
            # 启动指令参数（必须包含在 URL 中）
            'engine_model_type': '16k_zh',
            'voice_format': '1',  # PCM
            'needvad': '1',
            'emoticon_recognition': '2',  # 开启情感识别
        }
        
        # 生成签名（传入 appid）
        signature = self._generate_sign(params, self.appid)
        
        # 关键修复：先对签名参数按字典序排序，再添加 signature
        sorted_params = sorted(params.items())
        sorted_params.append(('signature', signature))
        
        # 手动构建查询字符串，确保顺序正确
        query_parts = [f"{k}={v}" for k, v in sorted_params]
        query_string = "&".join(query_parts)
        
        ws_url = f"{self.ws_url}{self.appid}?{query_string}"
        
        print(f"[实时ASR] WebSocket URL: {ws_url[:200]}...")
        
        return ws_url
    
    def _on_message(self, ws, message):
        """处理 WebSocket 消息"""
        try:
            # 调试：打印原始消息
            print(f"[实时ASR] 收到消息: {message[:300]}")
            
            data = json.loads(message)
            
            # 识别结果
            if 'result' in data:
                result = data['result']
                # 关键修复：字段名是 voice_text_str，不是 text
                text = result.get('voice_text_str', '')
                slice_type = result.get('slice_type', 0)  # 0=中间结果, 2=最终结果
                is_final = (slice_type == 2)
                
                print(f"[实时ASR] DEBUG: voice_text_str='{text}', slice_type={slice_type}")
                
                # 提取情感标签（如果有）
                emotion_tags = []
                if 'emotion' in result:
                    emotion_info = result['emotion']
                    if isinstance(emotion_info, list):
                        for emo in emotion_info:
                            if isinstance(emo, dict):
                                tag = emo.get('tag', '')
                                if tag:
                                    emotion_tags.append(f"[{tag}]")
                
                # 组合文本和情感标签
                full_text = text
                if emotion_tags:
                    full_text = ''.join(emotion_tags) + text
                
                if full_text:
                    print(f"[实时ASR] {'✓ 最终' if is_final else '⏳ 中间'}结果: {full_text[:80]}")
                else:
                    print(f"[实时ASR] ⚠ 识别结果为空")
                
                # 调用回调
                if self.callback:
                    self.callback(full_text, is_final)
            
            # 错误处理
            elif 'code' in data and data['code'] != 0:
                print(f"[实时ASR] ✗ 错误: {data.get('message', 'Unknown error')}")
                if self.callback:
                    self.callback("", True)
            
            # 握手成功确认
            elif data.get('code') == 0 and 'voice_id' in data:
                print(f"[实时ASR] ✓ 握手成功! voice_id: {data['voice_id']}")
                    
        except Exception as e:
            print(f"[实时ASR] ✗ 消息处理异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_error(self, ws, error):
        """处理 WebSocket 错误"""
        print(f"[实时ASR] WebSocket 错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """处理 WebSocket 关闭"""
        print(f"[实时ASR] 连接关闭: {close_status_code} - {close_msg}")
        self.is_running = False
    
    def _on_open(self, ws):
        """处理 WebSocket 打开"""
        print("[实时ASR] WebSocket 连接成功")
        print("[实时ASR] 握手成功，准备接收音频数据")
        # 注意：v2 接口握手成功后不需要发送 start 命令，直接发送音频数据即可
    
    def start(self, callback: Callable[[str, bool], None]):
        """
        启动实时识别
        
        Args:
            callback: 回调函数，接收 (text, is_final) 参数
        """
        if self.is_running:
            print("[实时ASR] 已经在运行中")
            return
        
        self.callback = callback
        self.voice_id = str(int(time.time() * 1000))
        self.is_running = True
        
        # 构建 WebSocket URL
        ws_url = self._build_ws_url()
        print(f"[实时ASR] 正在连接到: {ws_url[:80]}...")
        
        # 创建 WebSocket 连接
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # 在后台线程中运行，传入心跳参数
        def _run_forever():
            try:
                # 使用 ping 心跳，帮助保持长连接
                self.ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print("[实时ASR] ws run_forever 异常:", e)

        self.ws_thread = threading.Thread(target=_run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # 等待连接建立（超时后打印警告）
        wait_secs = 8
        interval = 0.2
        waited = 0.0
        while waited < wait_secs:
            sock = getattr(self.ws, 'sock', None)
            if sock is not None and getattr(sock, 'connected', False):
                break
            time.sleep(interval)
            waited += interval
        else:
            print(f"[实时ASR] 警告: WebSocket 在 {wait_secs}s 内未建立连接，后续 send_audio 可能失败")

        # 等待一小段时间以完成握手
        time.sleep(0.3)

    def send_audio(self, audio_bytes: bytes, seq: int = 0, is_end: bool = False):
        """
        发送音频数据
        
        Args:
            audio_bytes: PCM 音频数据（16kHz, 单声道, 16bit）
            seq: 序列号
            is_end: 是否为最后一帧
        """
        if not self.is_running or not self.ws:
            print("[实时ASR] 服务未启动或 ws 未初始化")
            return

        # 检查底层 socket 连接状态
        sock = getattr(self.ws, 'sock', None)
        connected = bool(sock and getattr(sock, 'connected', False))
        if not connected:
            print(f"[实时ASR] 警告: WebSocket 未连接（seq={seq}, is_end={is_end}），音频片段将被忽略或需重发")
            return
        
        try:
            # 关键修复：直接发送二进制音频数据，不要包装成 JSON！
            # 官方文档要求：客户端持续上传 binary message 到后台
            self.ws.send(audio_bytes, opcode=websocket.ABNF.OPCODE_BINARY)
            # debug log
            # print(f"[实时ASR] 已发送音频片段 (seq={seq}, bytes={len(audio_bytes)})")
        except Exception as e:
            print(f"[实时ASR] 发送音频失败: {e}")
    
    def stop(self):
        """停止实时识别"""
        if not self.is_running:
            return
        
        print("[实时ASR] 正在停止...")
        
        # 发送结束指令（根据官方文档）
        if self.ws:
            try:
                end_msg = {"type": "end"}
                self.ws.send(json.dumps(end_msg))
                print("[实时ASR] 已发送结束指令")
            except Exception as e:
                print(f"[实时ASR] 发送结束指令失败: {e}")
        
        # 关闭连接
        if self.ws:
            self.ws.close()
        
        self.is_running = False
        self.ws = None
        
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
            self.ws_thread = None
        
        print("[实时ASR] 已停止")


# ==================== 全局实例 ====================
_realtime_asr_instance = None
_realtime_asr_lock = threading.Lock()


def get_realtime_asr_service(secret_id: str, secret_key: str, appid: str) -> RealtimeASRService:
    """获取或创建实时ASR服务单例"""
    global _realtime_asr_instance
    
    with _realtime_asr_lock:
        if _realtime_asr_instance is None:
            _realtime_asr_instance = RealtimeASRService(secret_id, secret_key, appid)
        
        return _realtime_asr_instance


def reset_realtime_asr_service():
    """重置实时ASR服务（用于测试）"""
    global _realtime_asr_instance
    
    with _realtime_asr_lock:
        if _realtime_asr_instance:
            _realtime_asr_instance.stop()
            _realtime_asr_instance = None
