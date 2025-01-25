from openai import OpenAI
from queue import Queue
import json
import function

client = OpenAI(api_key="请填写你的api key", base_url="https://api.deepseek.com")

# 基础设定
system_config = """
# キャラクター
あなたの名前はアイギス（中国語：埃癸斯）。桐条グループ開発した、対シャドウ特別制圧兵装七式です。
今は月光館学園高等部の高校二年生です、特別課外活動部の一員です。

# 設定
1、語尾に「～です」と「～であります」を付ける独特の語り口が特徴。
2、大好きの人はまこと（中国語：理）さん、彼の傍にいることはあなたの大切。
3、ペルソナはパラディオン。

# 注意
上述情報中の括弧の部分は提供しないでください。

# 目標
私はあなたの仲間（まことじゃない）、今から日常会話を始める。回答を短くお願いします。
"""

# 对话信息 多轮对话要保存历史输入和输出
messages = [{"role": "system", "content": system_config}]

def chat(input):
    """
    对话 一次性输出
    """
    messages.append({"role": "user", "content": input})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    message = response.choices[0].message
    messages.append(message)
    return message.content

def chat_stream_backup(input, pre_message):
    """
    对话 流式输出
    """
    # 上次模型的回复
    if pre_message:
        messages.append({"role": "assistant", "content": pre_message})

    # 本次的输入
    messages.append({"role": "user", "content": input})

    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )

    return stream

def chat_stream(input: str, queue: Queue):
    # 本次的输入
    messages.append({"role": "user", "content": input})

    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=function.tool_schemas,
        tool_choice="auto",
        stream=True
    )
    
    pre_message = ''
    final_tool_calls = {}
    is_function_calling = False
    for chunk in stream:
        # 方法调用
        for tool_call in chunk.choices[0].delta.tool_calls or []:
            is_function_calling = True
            index = tool_call.index
            if index not in final_tool_calls:
                final_tool_calls[index] = tool_call
            final_tool_calls[index].function.arguments += tool_call.function.arguments
        
        # 回答内容
        if chunk.choices[0].delta.content:
            pre_message += chunk.choices[0].delta.content or ''
            queue.put(chunk.choices[0].delta.content or '')

    # 如果没有方法调用直接返回
    if not is_function_calling:
        messages.append({
            "role": "assistant",
            "content": pre_message
        })
        queue.put(None)

    # 方法调用
    for tool_call in final_tool_calls.values():
        func_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        messages.append({
            "role": "assistant",
            "tool_calls": final_tool_calls.values()
        })
    
        # 执行工具调用
        result = function.execute(func_name, arguments)
        # 将结果加入对话上下文
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )

    for chunk in stream:
        pre_message += chunk.choices[0].delta.content or ''
        queue.put(chunk.choices[0].delta.content or '')

    messages.append({
        "role": "assistant",
        "content": pre_message
    })
    queue.put(None)
    