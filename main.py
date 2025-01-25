import sys
sys.path.append('.')
sys.path.append('./service')
from datetime import datetime
from playsound import playsound
from queue import Queue
from threading import Thread
import time
from service.asr import load_whisper, transcribe_audio
from service.record import record_audio
from service.llm import chat_stream
from service.tts import to_speech_wav
from service.util import split_sentences


load_whisper()
input_path = './temp/'

print('')
print('======================================')
print('')

# 音频队列
audio_queue = Queue()

def audio_player():
    '''
    顺序播放队列中的音频
    '''
    while True:
        task = audio_queue.get()
        # None 表示结束信号
        if task is None:
            audio_queue.queue.clear()
            break

        try:
            playsound(task)
            # 让每句话之间有间隔
            time.sleep(0.5)
        except Exception as e:
            print(f'无法播放: {e}')

# 开始对话
pre_message = ''
while True:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    input_speech = input_path + timestamp + '.wav'

    record_audio(input_speech)
    input, language = transcribe_audio(input_speech)
    print('用户: ' + input)
    print()

    # 开启后台音频播放线程
    player_thread = Thread(target=audio_player)
    player_thread.start()

    # 调用大模型对话
    message_queue = Queue()
    chat_thread = Thread(target=chat_stream, args=(input, message_queue))
    chat_thread.start()
    sentence_buffer = ''
    print('埃癸斯: ', end='')
    while True:
        content = message_queue.get()
        if content == None:
            break
        print(content, end='')
        sentence_buffer += content

        # 检测并处理完整句子
        # 不要一次性整段做TTS 会很慢 发现一句就生成一句
        sentences = split_sentences(sentence_buffer)
        if sentences:
            for sentence in sentences[:-1]:
                if sentence:
                    speech_file = to_speech_wav(sentence, language)
                    audio_queue.put(speech_file)
            # 保留未完成的句子
            sentence_buffer = sentences[-1]

    # 处理剩余缓冲区内容
    rest = sentence_buffer.strip()
    if rest:
        speech_file = to_speech_wav(rest, language)
        audio_queue.put(speech_file)
        pre_message += rest
    
    # 等待对话结束
    chat_thread.join()

    # 等待音频播放结束
    audio_queue.put(None)
    player_thread.join()
    print()
    print()