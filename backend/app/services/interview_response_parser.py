import json
import re


class InterviewResponseParser:
    _LABEL_PATTERNS = [
        re.compile(r'（\s*追问\s*\d+\s*）'),
        re.compile(r'\(\s*追问\s*\d+\s*\)'),
        re.compile(r'第\s*\d+\s*题[:：]?'),
        re.compile(r'^\s*\d+[\.、]\s*', re.MULTILINE),
    ]
    _AIISH_BRIDGE_PATTERNS = [
        re.compile(r'^\s*(那我|那就|我再|我来)?追问一下[：:，,\s]*'),
        re.compile(r'^\s*继续追问一下[：:，,\s]*'),
        re.compile(r'^\s*我再补问一下[：:，,\s]*'),
    ]

    @staticmethod
    def _strip_code_fence(text):
        raw = (text or '').strip()
        if raw.startswith('```'):
            raw = re.sub(r'^```[a-zA-Z0-9]*\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
        return raw.strip()

    @staticmethod
    def _extract_json_block(text):
        raw = InterviewResponseParser._strip_code_fence(text)
        if raw.startswith('{') and raw.endswith('}'):
            return raw
        left = raw.find('{')
        right = raw.rfind('}')
        if left != -1 and right != -1 and right > left:
            return raw[left:right + 1]
        return raw

    @staticmethod
    def parse_structured_reply(raw_text):
        payload = {
            'internal_thought': '',
            'spoken_text': '',
            'follow_up_points': [],
            'should_end_interview': False,
        }
        block = InterviewResponseParser._extract_json_block(raw_text)
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                payload['internal_thought'] = str(parsed.get('internal_thought', '') or '').strip()
                payload['spoken_text'] = str(parsed.get('spoken_text', '') or '').strip()
                points = parsed.get('follow_up_points', [])
                if isinstance(points, list):
                    payload['follow_up_points'] = [str(x).strip() for x in points if str(x).strip()]
                payload['should_end_interview'] = bool(parsed.get('should_end_interview', False))
        except Exception:
            payload['spoken_text'] = str(raw_text or '').strip()
        return payload

    @staticmethod
    def sanitize_spoken_text(spoken_text, max_questions_per_turn=1):
        text = str(spoken_text or '').replace('[INTERVIEW_OVER]', '').strip()
        for pattern in InterviewResponseParser._LABEL_PATTERNS:
            text = pattern.sub('', text)
        for pattern in InterviewResponseParser._AIISH_BRIDGE_PATTERNS:
            text = pattern.sub('', text)
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n[ \t]+', '\n', text)
        text = re.sub(r'\n{2,}', '\n', text).strip()
        if not text:
            return '我们继续，你围绕刚才的问题补充一个具体例子：你的做法、指标结果和一次关键取舍是什么？'

        marks = ['？', '?']
        q_count = 0
        out_chars = []
        for ch in text:
            out_chars.append(ch)
            if ch in marks:
                q_count += 1
                if q_count >= max(1, int(max_questions_per_turn or 1)):
                    break
        truncated = ''.join(out_chars).strip()
        if q_count == 0:
            return text
        return truncated

    @staticmethod
    def build_ack_followup(last_ai_content, session_style='confident', max_questions_per_turn=1):
        last_question = str(last_ai_content or '').strip()
        if session_style == 'pressure':
            text = "收到，我们继续。刚才这个问题，请你直接给出一个可量化的做法和结果。"
        elif session_style == 'teaching':
            text = "好的，我们接着来。你就围绕刚才那题，按“问题-做法-结果”补充一个具体例子。"
        else:
            text = "好，我们继续。刚才那个点请你展开一下：你是怎么做的，结果如何？"
        if last_question and '？' in last_question:
            text = f"{text}重点回应你上一题里的关键追问。"
        return InterviewResponseParser.sanitize_spoken_text(text, max_questions_per_turn=max_questions_per_turn)
