from datetime import datetime, timedelta
from secrets import randbelow
from threading import Lock


class VerificationCodeService:
    _codes = {}
    _lock = Lock()
    _ttl_seconds = 300

    @classmethod
    def _build_key(cls, action, target):
        return f"{action}:{target.strip().lower()}"

    @classmethod
    def generate_and_store_code(cls, action, target):
        code = f"{randbelow(1000000):06d}"
        expire_at = datetime.utcnow() + timedelta(seconds=cls._ttl_seconds)
        key = cls._build_key(action, target)
        with cls._lock:
            cls._codes[key] = {"code": code, "expire_at": expire_at}
        return code

    @classmethod
    def verify_code(cls, action, target, code):
        key = cls._build_key(action, target)
        now = datetime.utcnow()
        with cls._lock:
            record = cls._codes.get(key)
            if not record:
                return False, "验证码不存在或已失效"
            if now > record["expire_at"]:
                cls._codes.pop(key, None)
                return False, "验证码已过期"
            if record["code"] != str(code).strip():
                return False, "验证码错误"
            cls._codes.pop(key, None)
            return True, "验证码校验通过"
