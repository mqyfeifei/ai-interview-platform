"""测试腾讯云 ASR WebSocket 连接"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('app/.env')

secret_id = os.getenv('TENCENT_SECRET_ID', '').strip()
secret_key = os.getenv('TENCENT_SECRET_KEY', '').strip()
appid = os.getenv('TENCENT_ASR_APP_ID', '').strip()

print("=" * 80)
print("腾讯云 ASR 连接测试")
print("=" * 80)
print(f"SecretId: {secret_id[:20]}... (长度: {len(secret_id)})")
print(f"SecretKey: {secret_key[:20]}... (长度: {len(secret_key)})")
print(f"AppID: {appid}")
print("=" * 80)

if not all([secret_id, secret_key, appid]):
    print("\n❌ 错误: 配置不完整")
    exit(1)

# 测试网络连接
print("\n[1] 测试网络连接...")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('asr.cloud.tencent.com', 443))
    sock.close()
    if result == 0:
        print("   ✓ 可以连接到 asr.cloud.tencent.com:443")
    else:
        print(f"   ✗ 无法连接 (错误码: {result})")
        print("   可能是网络问题（校园网/防火墙）")
except Exception as e:
    print(f"   ✗ 网络测试失败: {e}")

# 尝试使用官方 SDK 验证密钥
print("\n[2] 尝试使用腾讯云 SDK 验证密钥...")
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    
    cred = credential.Credential(secret_id, secret_key)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "aai.tencentcloudapi.com"
    
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    
    from tencentcloud.aai.v20180522 import aai_client
    client = aai_client.AaiClient(cred, "", clientProfile)
    
    # 尝试调用 CreateRecTask API（这个接口肯定存在）
    from tencentcloud.aai.v20180522.models import CreateRecTaskRequest
    req = CreateRecTaskRequest()
    req.EngineModelType = "16k_zh"
    req.ChannelNum = 1
    req.ResTextFormat = 0
    req.SourceType = 0
    
    resp = client.CreateRecTask(req)
    print(f"   ✓ SDK 认证成功！")
    print(f"   Response: {resp.to_json_string()[:200]}")
    
except Exception as e:
    error_msg = str(e)
    if "AuthFailure" in error_msg or "InvalidParameter.SecretId" in error_msg or "InvalidParameter.SecretKey" in error_msg:
        print(f"   ✗ 认证失败: {error_msg}")
        print("   → SecretId 或 SecretKey 不正确")
    elif "Network" in error_msg or "timeout" in error_msg.lower():
        print(f"   ✗ 网络错误: {error_msg}")
        print("   → 可能是校园网限制了访问")
    else:
        print(f"   ⚠ 其他错误: {error_msg}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
