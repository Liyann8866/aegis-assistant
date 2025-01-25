import pyaudio
import torch
import numpy as np
import wave
import time
import silero_vad

# 参数配置
SAMPLING_RATE = 16000
WINDOW_SIZE_SAMPLES = 512  # 对应16kHz采样率
SILENCE_TIMEOUT = 1.0      # 静音超时1秒
MIN_RECORDING_DURATION = 0.5  # 最小有效录音时长

# 加载Silero VAD模型
model = silero_vad.load_silero_vad()
model.reset_states()

def record_audio(filename):
    """
    VAD检测并录音
    """
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLING_RATE,
        input=True,
        frames_per_buffer=WINDOW_SIZE_SAMPLES
    )

    # 录音控制变量
    recording = False
    audio_buffer = []
    last_speech_time = None

    print("等待语音活动...")
    try:
        while True:
            # 读取音频数据块
            chunk = stream.read(WINDOW_SIZE_SAMPLES, exception_on_overflow=False)
            audio_int16 = np.frombuffer(chunk, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # VAD检测
            with torch.no_grad():
                speech_prob = model(torch.from_numpy(audio_float32), SAMPLING_RATE).item()

            current_time = time.time()
            
            if not recording:
                # 如果检测到语音 开始录音
                if speech_prob > 0.5:
                    print("检测到语音\n")
                    recording = True
                    audio_buffer = [chunk]
                    last_speech_time = current_time
            else:
                # 继续录音
                audio_buffer.append(chunk)
                
                if speech_prob > 0.5:
                    last_speech_time = current_time
                    
                # 检查静音是否超时
                if current_time - last_speech_time >= SILENCE_TIMEOUT:
                    recording = False
                    duration = current_time - (last_speech_time - SILENCE_TIMEOUT)
                    
                    # 保存有效录音
                    if duration >= MIN_RECORDING_DURATION:
                        with wave.open(filename, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                            wf.setframerate(SAMPLING_RATE)
                            wf.writeframes(b''.join(audio_buffer))
                        return
                    else:
                        print(f"录音过短（{duration:.2f}秒），已丢弃")
                        recording = False
                        audio_buffer = []
                        last_speech_time = None
                        model.reset_states()

    except KeyboardInterrupt:
        print("\n停止录音")
    finally:
        model.reset_states()
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    output_filename = "./temp/output.wav"
    record_audio(output_filename)