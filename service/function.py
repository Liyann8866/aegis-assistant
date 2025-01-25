import requests
from typing import Dict, Callable
import subprocess
import os
import difflib



def get_current_weather(location: str):
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data["current_condition"][0]
        return {
            "location": location,
            "temperature": current["temp_C"],
            "description": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"]
        }
    except Exception as e:
        return {"error": str(e)}
    
def start_calculator():
    try:
        subprocess.Popen('calc.exe')
        return "计算器已启动成功"
    except Exception as e:
        print(f"启动计算器错误，请检查: {e}")
        return "启动计算器错误，请检查"

def play_music(music: str = ''):
    try:
        music_directory = os.path.expandvars("%USERPROFILE%/Music")
        supported_formats = ('.mp3', '.wav', '.m4a', '.flac')

        # 获取所有匹配的音乐文件
        music_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(music_directory)
            for file in files
            if file.endswith(supported_formats)
        ]

        if not music_files:
            return "没有找到音乐文件"

        # 如果没有指定音乐名称，播放第一个文件
        if not music:
            os.startfile(music_files[0])
            return f"执行成功，已开始播放: {os.path.basename(music_files[0])}"

        # 查找最相似的文件
        most_similar_file = max(
            music_files,
            key=lambda f: difflib.SequenceMatcher(
                None, os.path.splitext(os.path.basename(f))[0].lower(), music.lower()
            ).ratio()
        )

        # 播放音乐
        os.startfile(most_similar_file)
        return f"执行成功，已开始播放: {os.path.basename(most_similar_file)}"

    except Exception as e:
        print(f"播放错误: {e}")
        return "播放错误，请检查"


# 注册上述方法
TOOL_CONFIG = [
    {
        "name": "get_current_weather",
        "function": get_current_weather,
        "description": "获取指定城市的当前天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市的英文名称"
                }
            },
            "required": ["location"]
        },
    },
    {
        "name": "start_calculator",
        "function": start_calculator,
        "description": "启动计算器",
        "parameters": {
            "type": "object",
            "properties": {}
        },
    },
    {
        "name": "play_music",
        "function": play_music,
        "description": "播放音乐，不指定歌曲名则参数留空",
        "parameters": {
            "type": "object",
            "properties": {
                "music": {
                    "type": "string",
                    "description": "歌曲名"
                }
            }
        },
    },
]



# 通用方法调用部分
tool_map: Dict[str, Callable] = {}
tool_schemas = []

# 初始化工具映射和schema
for config in TOOL_CONFIG:
    tool_map[config["name"]] = config["function"]
    tool_schemas.append({
        "type": "function",
        "function": {
            "name": config["name"],
            "description": config["description"],
            "parameters": config["parameters"]
        }
    })

def execute(func_name: str, arguments: dict):
    """通用函数执行方法"""
    if func_name not in tool_map:
        return {"error": f"Function {func_name} not found"}
    
    try:
        return tool_map[func_name](**arguments)
    except Exception as e:
        return {"error": str(e)}
