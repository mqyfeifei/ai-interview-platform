from openai import OpenAI
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

    def generate_reply(self, messages, stream=False):
        """
        调用大模型生成回复
        :param messages: 对话上下文列表，例如 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        :param stream: 是否流式输出
        """
        try:
            # 构建请求参数
            request_params = {
                'model': self.model,
                'messages': messages,
                'stream': stream,
                'temperature': 0.7
            }

            response = self.client.chat.completions.create(**request_params)
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            # 此处应接入日志系统记录异常
            raise RuntimeError(f"LLM 调用失败: {str(e)}")