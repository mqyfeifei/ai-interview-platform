"""
严格按照腾讯云官方文档示例验证签名算法
参考: https://cloud.tencent.com/document/product/1093/48982
"""
import os
import hmac
import hashlib
import base64
import urllib.parse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('app/.env')

secret_id = os.getenv('TENCENT_SECRET_ID', '').strip()
secret_key = os.getenv('TENCENT_SECRET_KEY', '').strip()
appid = os.getenv('TENCENT_ASR_APP_ID', '').strip()

print("=" * 80)
print("腾讯云 WebSocket ASR 签名验证")
print("=" * 80)
print(f"SecretId: {secret_id}")
print(f"SecretKey: {secret_key} (长度: {len(secret_key)})")
print(f"AppID: {appid}")
print("=" * 80)

# 模拟官方文档的参数
timestamp = 1776080000
expired = timestamp + 24 * 3600
nonce = 123456789
voice_id = "test_voice_123"

print(f"\n测试参数:")
print(f"  timestamp: {timestamp}")
print(f"  expired: {expired}")
print(f"  nonce: {nonce}")
print(f"  voice_id: {voice_id}")

# 步骤1: 准备参数（按字典序排序）
params = {
    'secretId': secret_id,
    'timestamp': str(timestamp),
    'expired': str(expired),
    'nonce': str(nonce),
    'voice_id': voice_id,
}

print(f"\n[步骤1] 参数（按字典序排序）:")
sorted_params = sorted(params.items())
for k, v in sorted_params:
    print(f"  {k}={v}")

# 步骤2: 拼接查询字符串
query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
print(f"\n[步骤2] 查询字符串:")
print(f"  {query_string}")

# 步骤3: 生成签名原文（注意：不包含 wss:// 协议头，但包含 appid）
sign_str = f"asr.cloud.tencent.com/asr/v2/{appid}?{query_string}"
print(f"\n[步骤3] 签名原文:")
print(f"  {sign_str}")

# 步骤4: HMAC-SHA1 签名
sign = hmac.new(
    secret_key.encode('utf-8'),
    sign_str.encode('utf-8'),
    hashlib.sha1
).digest()

print(f"\n[步骤4] HMAC-SHA1 签名（二进制）:")
print(f"  长度: {len(sign)} bytes")

# 步骤5: Base64 编码
signature = base64.b64encode(sign).decode('utf-8')
print(f"\n[步骤5] Base64 编码后:")
print(f"  {signature}")

# 步骤6: URL 编码
signature_encoded = urllib.parse.quote(signature, safe='')
print(f"\n[步骤6] URL 编码后:")
print(f"  {signature_encoded}")

# 构建完整 URL
final_params = dict(sorted_params)
final_params['signature'] = signature_encoded
final_query = "&".join([f"{k}={v}" for k, v in sorted(final_params.items())])
ws_url = f"wss://asr.cloud.tencent.com/asr/v2/{appid}?{final_query}"

print(f"\n[最终] WebSocket URL:")
print(f"  {ws_url[:200]}...")

print("\n" + "=" * 80)
print("✅ 签名计算完成！")
print("=" * 80)
print("\n请复制上面的 URL 到浏览器或 WebSocket 客户端测试连接")
print("如果仍然报'签名错误'，请检查:")
print("  1. SecretKey 是否完整（应该 40+ 字符）")
print("  2. 是否有额外的空格或换行符")
print("  3. AppID 是否正确")
