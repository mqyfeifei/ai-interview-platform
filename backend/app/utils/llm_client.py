import time
from openai import OpenAI, APIConnectionError, APITimeoutError
from flask import current_app


class DeepSeekClient:
    def __init__(self):
        # 检查是否使用阿里云百炼平台
        if current_app.config.get('USE_ALIYUN_DASHSCOPE', False):
            self.client = OpenAI(
                api_key=current_app.config['DASHSCOPE_API_KEY'],
                base_url=current_app.config['DASHSCOPE_BASE_URL']
            )
            self.model = current_app.config['DASHSCOPE_MODEL_NAME']
        else:
            # 保持原有 DeepSeek 配置
            self.client = OpenAI(
                api_key=current_app.config['DEEPSEEK_API_KEY'],
                base_url=current_app.config['DEEPSEEK_BASE_URL']
            )
            self.model = current_app.config['LLM_MODEL_NAME']

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return True
        message = str(exc).lower()
        retryable_keywords = (
            'connection error',
            'timed out',
            'timeout',
            'unexpected eof',
            'eof occurred in violation of protocol',
            'connection reset',
            'temporary failure',
            '503',
            '502',
            '504',
        )
        return any(keyword in message for keyword in retryable_keywords)

    def generate_reply(self, messages, stream=False, temperature=0.7):
        """
        调用大模型生成回复
        :param messages: 对话上下文列表，例如 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        :param stream: 是否流式输出
        """
        # 构建请求参数
        request_params = {
            'model': self.model,
            'messages': messages,
            'stream': stream,
            'temperature': temperature
        }
        max_retries = max(1, int(current_app.config.get('LLM_MAX_RETRIES', 3)))
        backoff_seconds = max(0.1, float(current_app.config.get('LLM_RETRY_BACKOFF_SECONDS', 1.0)))

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(**request_params)
                if stream:
                    return response
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                retryable = self._is_retryable_exception(e)
                can_retry = retryable and attempt < max_retries
                print(
                    f"[DeepSeekClient] 调用失败（{attempt}/{max_retries}）："
                    f"{type(e).__name__}: {e}"
                )
                if not can_retry:
                    break
                time.sleep(backoff_seconds * attempt)

        raise RuntimeError(f"LLM 调用失败: {last_error}") from last_error
