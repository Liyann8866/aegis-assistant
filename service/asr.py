import torch
from faster_whisper import WhisperModel

model: WhisperModel = None

def load_whisper():
    """
    加载 Whisper 模型
    """
    global model
    print(f"加载 Whisper 模型...")
    model = WhisperModel("large-v3", device="cuda" if torch.cuda.is_available() else "cpu", compute_type="float16")

def transcribe_audio(file_path):
    """
    使用 fast-whisper 识别音频文件
    """
    global model
    # 识别音频
    # print(f"正在识别音频文件: {file_path}")
    segments, info = model.transcribe(file_path)
    text = ''.join(map(lambda s: s.text, segments))

    return text, info.language

if __name__ == "__main__":
    load_whisper()
    # 示例音频文件路径
    audio_file_path = "./temp/20250120210408.wav"
    text, language = transcribe_audio(audio_file_path)
    print("识别结果:")
    print(text)
    print(language)