import json
import re

from app import create_app
from app.models.interview import InterviewChat
from app.utils.llm_client import DeepSeekClient


def clean_json_block(raw_text):
    text = str(raw_text or '').strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def main():
    interview_id = 15
    app = create_app('development')

    with app.app_context():
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp.asc()).all()

        print('INTERVIEW_ID', interview_id)
        print('CHAT_COUNT', len(chats))

        if not chats:
            print('NO_CHAT_RECORDS_FOUND')
            return

        pairs = []
        analysis_index = 1
        for idx, chat in enumerate(chats):
            if chat.role != 'ai':
                continue

            user_reply = None
            for j in range(idx + 1, len(chats)):
                if chats[j].role == 'user':
                    user_reply = chats[j]
                    break
                if chats[j].role == 'ai':
                    break

            pairs.append({
                'index': analysis_index,
                'questionChatId': chat.id,
                'answerChatId': user_reply.id if user_reply else None,
                'question': chat.content or '',
                'answer': (user_reply.content if user_reply else '') or ''
            })
            analysis_index += 1

        print('PAIR_COUNT', len(pairs))

        llm = DeepSeekClient()
        system_prompt = (
            '你是一名资深技术面试官。请仅对用户回答进行技术分析，不要打分。'
            '必须返回 JSON 数组，每项结构：{"index":1,"analysis":"..."}。'
            'analysis 用中文 2-4 句，包含：准确性、深度、遗漏点、改进建议。'
        )
        user_prompt = (
            '请逐条分析以下问答中的用户回答：\n' +
            json.dumps([
                {'index': p['index'], 'question': p['question'], 'answer': p['answer']}
                for p in pairs
            ], ensure_ascii=False)
        )

        response_text = llm.generate_reply([
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ])

        cleaned = clean_json_block(response_text)
        parsed = json.loads(cleaned)

        analysis_map = {}
        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                idx = item.get('index')
                try:
                    idx = int(idx)
                except Exception:
                    continue
                analysis_map[idx] = (item.get('analysis') or '').strip()

        result = []
        for pair in pairs:
            result.append({
                'index': pair['index'],
                'questionChatId': pair['questionChatId'],
                'answerChatId': pair['answerChatId'],
                'question': pair['question'],
                'answer': pair['answer'],
                'analysis': analysis_map.get(pair['index'], 'AI分析缺失')
            })

        print('AI_ANALYSIS_RESULT')
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
