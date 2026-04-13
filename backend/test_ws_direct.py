"""直接测试 WebSocket 连接"""
import websocket
import json
import time
import sys

# 使用刚才计算的 URL（你需要替换成最新的）
# 注意：timestamp 会过期，每次运行需要重新生成
import os
import hmac
import hashlib
import base64
import urllib.parse
import random
from dotenv import load_dotenv

load_dotenv('app/.env')

secret_id = os.getenv('TENCENT_SECRET_ID', '').strip()
secret_key = os.getenv('TENCENT_SECRET_KEY', '').strip()
appid = os.getenv('TENCENT_ASR_APP_ID', '').strip()

# 生成新的时间戳
timestamp = int(time.time())
expired = timestamp + 24 * 3600
nonce = random.randint(100000000, 999999999)
voice_id = str(int(time.time() * 1000))

# 准备参数（包含启动指令参数）
params = {
    'secretId': secret_id,
    'timestamp': str(timestamp),
    'expired': str(expired),
    'nonce': str(nonce),
    'voice_id': voice_id,
    # 启动指令参数
    'engine_model_type': '16k_zh',
    'voice_format': '1',
    'needvad': '1',
    'emoticon_recognition': '2',
}

# 按字典序排序
sorted_params = sorted(params.items())
query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

# 生成签名原文
sign_str = f"asr.cloud.tencent.com/asr/v2/{appid}?{query_string}"

# HMAC-SHA1
sign = hmac.new(
    secret_key.encode('utf-8'),
    sign_str.encode('utf-8'),
    hashlib.sha1
).digest()

# Base64 + URL 编码
signature = base64.b64encode(sign).decode('utf-8')
signature_encoded = urllib.parse.quote(signature, safe='')

# 构建最终 URL
final_params = dict(sorted_params)
final_params['signature'] = signature_encoded
final_query = "&".join([f"{k}={v}" for k, v in sorted(final_params.items())])
ws_url = f"wss://asr.cloud.tencent.com/asr/v2/{appid}?{final_query}"

print("=" * 80)
print("WebSocket 连接测试")
print("=" * 80)
print(f"URL: {ws_url[:150]}...")
print("=" * 80)

# 接收消息
def on_message(ws, message):
    print(f"\n[收到消息] {message}")
    try:
        data = json.loads(message)
        if 'code' in data:
            print(f"  Code: {data['code']}")
            print(f"  Message: {data.get('message', 'N/A')}")
    except:
        pass

def on_error(ws, error):
    print(f"\n[错误] {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"\n[连接关闭] Code: {close_status_code}, Message: {close_msg}")

def on_open(ws):
    print("\n[✓] WebSocket 连接成功！")
    print("[✓] 握手成功，准备接收音频数据")
    print("[→] 注意：v2 接口不需要发送 start 命令")
    print("[→] 请直接发送音频数据或等待超时断开\n")

# 创建连接
ws = websocket.WebSocketApp(
    ws_url,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

print("\n[→] 正在连接...")
ws.run_forever()
