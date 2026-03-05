from openai import OpenAI
from flask import current_app

class DeepSeekClient:
    def __init__(self):
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=0.7
            )
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            # 此处应接入日志系统记录异常
            raise RuntimeError(f"LLM 调用失败: {str(e)}")