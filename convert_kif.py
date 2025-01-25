import re

def clean_kifu(lines):
    cleaned_moves = []
    
    for line in lines:
        line = line.strip()

        if not line or line.startswith("*"):  # 空行やコメント行をスキップ
            continue

        # 🔍 `(\d+:\d+/\d+:\d+)` の時間情報を削除
        line = re.sub(r'\(\d+:\d+/\d+:\d+\)', '', line)

        # 🔍 **正しい指し手の行だけ取得**
        if re.match(r'^\d+\s+[１-９][一二三四五六七八九][歩香桂銀金角飛玉]+', line):
            cleaned_moves.append(line)

    return cleaned_moves


with open("kifs/kif.kif", "r", encoding="utf-8") as f:
    lines = f.readlines()

cleaned_moves = clean_kifu(lines)

# 🔄 結果をファイルに保存
with open("translated_kifs/cleaned_kif.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(cleaned_moves))