import re
def f(t):
    p = re.compile(r'[^\u4e00-\u9fffa-zA-Z0-9，。！？；、：“”《》（）\.,!?;\'\"()\[\]\-\+\s\n·—－￥]')
    return p.sub('', t)
print('Length:', len(f('你好，很高兴和你聊聊')))
