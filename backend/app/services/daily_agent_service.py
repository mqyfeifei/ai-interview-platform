import datetime
import html
import re
import time
import threading

from flask import current_app

from app.models.user import User
from app.services.learning_service import LearningService
from app.services.notification_service import NotificationService
from app.services.trending_service import TrendingService


class DailyAgentService:
    @staticmethod
    def _create_llm():
        try:
            from langchain.chat_models import init_chat_model
        except ImportError as exc:
            raise RuntimeError(
                'LangChain 未安装或未安装 provider 集成包，请执行: pip install langchain langchain-openai langchain-deepseek'
            ) from exc

        config = current_app.config
        if config.get('USE_ALIYUN_DASHSCOPE'):
            model_name = config.get('DASHSCOPE_MODEL_NAME', 'qwen3-max')
            api_key = config.get('DASHSCOPE_API_KEY')
            api_base = config.get('DASHSCOPE_BASE_URL')
            return init_chat_model(
                model_name,
                model_provider='openai',
                openai_api_key=api_key,
                openai_api_base=api_base,
                temperature=0.65,
            )

        model_name = config.get('LLM_MODEL_NAME', 'deepseek-chat')
        api_key = config.get('DEEPSEEK_API_KEY')
        api_base = config.get('DEEPSEEK_BASE_URL')
        return init_chat_model(
            model_name,
            model_provider='deepseek',
            api_key=api_key,
            base_url=api_base,
            temperature=0.65,
        )

    @staticmethod
    def get_trending_headlines(limit=4):
        try:
            topics = TrendingService.get_trending_topics('default', limit)
            headlines = [
                (item.get('title') or item.get('text') or '').strip()
                for item in topics if isinstance(item, dict)
            ]
            return [h for h in headlines if h][:limit] or ['暂无技术热榜，请稍后查看']
        except Exception as ex:
            current_app.logger.warning('获取技术热榜失败：%s', ex)
            return ['暂无技术热榜，请稍后查看']

    @staticmethod
    def get_trending_topics(limit=4):
        try:
            topics = TrendingService.get_trending_topics('default', limit)
            return [item for item in topics if isinstance(item, dict)]
        except Exception as ex:
            current_app.logger.warning('获取技术热榜失败：%s', ex)
            return []

    @staticmethod
    def _trending_headlines_tool():
        headlines = DailyAgentService.get_trending_headlines()
        return '\n'.join([f'- {h}' for h in headlines])

    @staticmethod
    def _build_email_html(body: str, topics: list):
        if not isinstance(body, str):
            body = str(body)

        title_to_url = {}
        for item in topics:
            title = (item.get('title') or item.get('text') or '').strip()
            url = item.get('url')
            if title and url:
                title_to_url[title] = url

        html_lines = []
        for line in body.splitlines():
            stripped = line.lstrip()
            if stripped.startswith('- '):
                content = stripped[2:].strip()
                url = title_to_url.get(content)
                if url:
                    prefix = line[:len(line) - len(stripped)]
                    html_lines.append(
                        f"{html.escape(prefix)}- <a href=\"{html.escape(url, quote=True)}\">{html.escape(content)}</a>"
                    )
                    continue
            html_lines.append(html.escape(line))

        return '<br>'.join(html_lines)

    @staticmethod
    def _get_user_plan_tool(user_id: int):
        plan = LearningService.get_daily_plan(user_id)
        return DailyAgentService._format_plan(plan)

    @staticmethod
    def _create_agent_executor(llm, system_prompt: str | None = None):
        try:
            from langchain.agents.factory import create_agent
            from langchain.tools import tool
        except ImportError as exc:
            raise RuntimeError(
                'LangChain 未安装或未安装 agent 相关模块，请执行: pip install langchain langchain-openai langchain-deepseek'
            ) from exc

        @tool(description='获取当前学习中心技术热榜标题，返回格式化的中文热点摘要。')
        def get_trending_headlines() -> str:
            headlines = DailyAgentService.get_trending_headlines()
            return '\n'.join([f'- {h}' for h in headlines])

        @tool(description='根据 user_id 查询用户的学习计划，并返回格式化的任务摘要。')
        def get_user_learning_plan(user_id: int) -> str:
            plan = LearningService.get_daily_plan(user_id)
            return DailyAgentService._format_plan(plan)

        tools = [get_trending_headlines, get_user_learning_plan]
        return create_agent(
            llm,
            tools=tools,
            system_prompt=system_prompt,
            debug=False,
        )

    @staticmethod
    def _format_plan(plan):
        lines = []
        if not plan or not plan.get('tasks'):
            return '今天没有规划到学习任务，您可以先浏览学习中心获取推荐。'

        for idx, task in enumerate(plan['tasks'], start=1):
            status = '✅' if task.get('done') else '☐'
            title = task.get('title') or f'任务 {idx}'
            lines.append(f'- {status}{title} ')
        return '\n'.join(lines)

    @staticmethod
    def _sanitize_agent_text(text):
        if not isinstance(text, str):
            return text

        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)
        text = re.sub(r'(?m)^\*\s+', '- ', text)
        text = re.sub(r'(?m)^\+\s+', '- ', text)
        text = re.sub(r'(?m)^>\s*', '', text)
        text = re.sub(r'(?m)^#{1,6}\s*', '', text)
        text = text.replace('*', '')
        return text.strip()

    @staticmethod
    def _extract_agent_text(result):

        # 情况 1：如果 result 直接就是字符串
        if isinstance(result, str):
            return DailyAgentService._sanitize_agent_text(result)
    
    # 情况 2：Agent 的标准返回通常包含 'messages' 列表
        if isinstance(result, dict):
        # 检查是否有 'messages' 键，AI 的最新回复通常在最后一条
            messages = result.get('messages')
            if isinstance(messages, list) and len(messages) > 0:
            # 逆序查找，找最新的 AI 消息
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get('type') == 'ai':
                        content = msg.get('content')
                        if isinstance(content, str):
                            return DailyAgentService._sanitize_agent_text(content)
                # 兼容 LangChain 对象模式
                    elif hasattr(msg, 'content'):
                        return DailyAgentService._sanitize_agent_text(str(msg.content))
        
        # 情况 3：某些配置下结果直接在 'output' 或 'return_values' 中
            if 'output' in result:
                return DailyAgentService._sanitize_agent_text(str(result['output']))
            if 'return_values' in result and 'output' in result['return_values']:
                return DailyAgentService._sanitize_agent_text(str(result['return_values']['output']))

    # 情况 4：兜底逻辑 - 尝试直接转字符串，但尽量避免走到这一步
    # 如果走到这一步，说明上面的结构没匹配到，result 可能是包含提示词的 Agent 对象
        return DailyAgentService._sanitize_agent_text(str(result))

    @staticmethod
    def generate_daily_message(user):
        system_prompt = (
    "你是一个专业的智能助理。请根据用户数据生成一份美观的日报。\n"
    "**重要格式要求：**\n"
    "1. 每个主要板块（如概览、清单、热点）之间必须空一行。\n"
    "2. 列表项每项必须单独一行，严禁使用逗号分隔。\n"
    "3. 请保持语气专业且亲切。\n"
    "4. 输出请不要包含 Markdown 标记，如 **、__、*、#、```。\n"
    "5. 问候语请根据当前发送时间选择，例如“早上好”、“下午好”或“晚上好”，不要写固定的“下午好”。\n\n"
    "请按照以下结构输出：\n"
    "👋 你好，用户！\n\n"
    "📅 **今日学习概览**\n"
    "- 🎯 今日计划：共 **{total}** 项\n"
    "- ✅ 当前进度：已完成 **{done}** 项\n\n"
    "📝 **待办清单**\n"
    "{todo_list}\n\n"
    "🔥 **技术热榜速递**\n"
    "{hot_topics}\n\n"
    "💡 **小贴士**\n"
    "{tip}"
)
        user_content = (
            f'用户信息：用户名={user.username or "未知"}，邮箱={user.email or "未设置"}。\n'
            f'用户 ID：{user.id}\n'
            f'当前时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
            '请生成一段温暖、简洁、鼓励用户完成学习的提醒文案，包含学习计划摘要和热点概要。鼓励用语要求体现对于拿到理想offer的期待和信心。'
        )
        llm = DailyAgentService._create_llm()
        agent = DailyAgentService._create_agent_executor(llm, system_prompt=system_prompt)
        result = agent.invoke({
            'messages': [
                {'type': 'human', 'content': user_content}
            ]
        })
        return DailyAgentService._extract_agent_text(result)

    @staticmethod
    def generate_evening_reminder(user, undone_tasks):
        if not undone_tasks:
            return None

        titles = '\n'.join([f'- {task.get("title")}' for task in undone_tasks[:10]])
        system_prompt = (
    "你是一个专业的智能助理。请根据用户数据生成一份美观的日报。\n"
    "**重要格式要求：**\n"
    "1. 每个主要板块（如概览、清单、热点）之间必须空一行。\n"
    "2. 列表项每项必须单独一行，严禁使用逗号分隔。\n"
    "3. 请保持语气专业且亲切。\n"
    "4. 输出请不要包含 Markdown 标记，如 **、__、*、#、```。\n"
    "5. 问候语请根据当前发送时间选择，例如“早上好”、“下午好”或“晚上好”，不要写固定的“下午好”。\n\n"
    "请按照以下结构输出：\n"
    "👋 你好，用户！\n\n"
    "📅 **今日学习概览**\n"
    "- 🎯 今日计划：共 **{total}** 项\n"
    "- ✅ 当前进度：已完成 **{done}** 项\n\n"
    "📝 **待办清单**\n"
    "{todo_list}\n\n"
    "🔥 **技术热榜速递**\n"
    "{hot_topics}\n\n"
    "💡 **小贴士**\n"
    "{tip}"
)
        user_content = (
            f'用户：{user.username or "用户"}\n'
            f'当前时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
            f'以下是今天尚未完成的任务：\n{titles}\n'
            '请生成一段简洁友好的提醒文案，并鼓励用户明天继续坚持。'
        )
        llm = DailyAgentService._create_llm()
        agent = DailyAgentService._create_agent_executor(llm, system_prompt=system_prompt)
        result = agent.invoke({
            'messages': [
                {'type': 'human', 'content': user_content}
            ]
        })
        return DailyAgentService._extract_agent_text(result)

    @staticmethod
    def _send_user_summary(user):
        if not user.email:
            current_app.logger.info('用户 %s 未配置邮箱，跳过早晨推送。', user.id)
            return
        body = DailyAgentService.generate_daily_message(user)
        topics = DailyAgentService.get_trending_topics()
        html_body = DailyAgentService._build_email_html(body, topics)
        NotificationService.send_email(user.email, '今日学习计划与热点', body, html_body=html_body)

    @staticmethod
    def _send_user_reminder(user):
        plan = LearningService.get_daily_plan(user.id)
        undone = [task for task in plan.get('tasks', []) if not task.get('done')]
        if not undone:
            current_app.logger.info('用户 %s 今日全部任务已完成，跳过晚间提醒。', user.id)
            return
        body = DailyAgentService.generate_evening_reminder(user, undone)
        if body:
            topics = DailyAgentService.get_trending_topics()
            html_body = DailyAgentService._build_email_html(body, topics)
            NotificationService.send_email(user.email, '今晚学习提醒：未完成任务', body, html_body=html_body)

    @staticmethod
    def send_daily_summaries():
        users = User.query.filter_by(is_active=True).all()
        for user in users:
            try:
                DailyAgentService._send_user_summary(user)
            except Exception as ex:
                current_app.logger.exception('早晨推送失败，用户 %s：%s', user.id, ex)

    @staticmethod
    def send_evening_reminders():
        users = User.query.filter_by(is_active=True).all()
        for user in users:
            try:
                DailyAgentService._send_user_reminder(user)
            except Exception as ex:
                current_app.logger.exception('晚间提醒失败，用户 %s：%s', user.id, ex)


class AgentScheduler:
    @staticmethod
    def start(app):
        thread = threading.Thread(target=AgentScheduler._run, args=(app,), daemon=True)
        thread.start()

    @staticmethod
    def _run(app):
        with app.app_context():
            while True:
                now = datetime.datetime.now()
                today_8am = now.replace(hour=5, minute=49, second=0, microsecond=0)
                today_8pm = now.replace(hour=20, minute=0, second=0, microsecond=0)

                if now < today_8am:
                    target = today_8am
                    action = DailyAgentService.send_daily_summaries
                elif now < today_8pm:
                    target = today_8pm
                    action = DailyAgentService.send_evening_reminders
                else:
                    target = (today_8am + datetime.timedelta(days=1))
                    action = DailyAgentService.send_daily_summaries

                wait_seconds = (target - now).total_seconds()
                if wait_seconds > 0:
                    time.sleep(wait_seconds)

                try:
                    action()
                except Exception as ex:
                    current_app.logger.exception('AgentScheduler 执行任务失败：%s', ex)

                time.sleep(60)
