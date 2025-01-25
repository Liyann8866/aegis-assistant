import re

def split_sentences(text):
    """
    根据标点分割句子，并保留最后一句未完成的语句
    """
    # 防小数点被切分 但如果是英语句子且以数字结尾会有句子粘连的问题
    parts = re.split(r'([。！？\!\?]|(?<!\d)\.(?!\d))', text)
    spilts = [parts[i].strip() + parts[i+1] for i in range(0, len(parts) - 1, 2) if parts[i].strip()]
    spilts.append(parts[-1].strip())
    return spilts