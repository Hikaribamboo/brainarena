import os
import re

# フォルダのパス
KIFS_FOLDER = "kifs"
SFEN_OUTPUT_FOLDER = "sfen_maker_1/output_sfens"
SFEN_OUTPUT_FILE = os.path.join(SFEN_OUTPUT_FOLDER, "output.sfen")

# USI 変換用辞書
USI_PIECES = {
    "歩": "P", "香": "L", "桂": "N", "銀": "S",
    "金": "G", "角": "B", "飛": "R", "王": "K"
}

trans_file1 = {'一': "a", '二': "b", '三': "c", '四': "d", '五': "e", '六': "f", '七': "g", '八': "h", '九': "i"}
trans_file2 = {'1': "a", '2': "b", '3': "c", '4': "d", '5': "e", '6': "f", '7': "g", '8': "h", '9': "i"}
trans_file3 = {'１': "1", '２': "2", '３': "3", '４': "4", '５': "5", '６': "6", '７': "7", '８': "8", '９': "9"}

# KIF ファイルを正規化（不要な情報削除）
def clean_kifu(kif_path):
    """ KIFファイルを読み込み、指し手のみを抽出 """
    cleaned_moves = []
    
    with open(kif_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line or line.startswith("*"):  # 空行やコメント行をスキップ
            continue

        # 🔍 `(\d+:\d+/\d+:\d+)` の時間情報を削除
        line = re.sub(r'\(\d+:\d+/\d+:\d+\)', '', line)

        # 🔍 指し手の行だけ取得
        if re.match(r'^\d+\s+[１-９][一二三四五六七八九][歩香桂銀金角飛玉と馬龍]*(成桂|成銀|成香)?+', line):
            cleaned_moves.append(line)

    return cleaned_moves


# SFEN 形式に変換
def process_sfen(cleaned_moves):
    """ 指し手を SFEN 形式に変換 """
    result = "position startpos moves "
    
    for line in cleaned_moves:
        space_index = line.index(" ")
        moved_file = line[space_index + 1]  # 移動後の筋
        moved_rank = line[space_index + 2]

        if line[space_index + 4] == "(":
            before_file = line[space_index + 5]  # 移動前の筋
            before_rank = line[space_index + 6]
        else:
            before_file = line[space_index + 6]
            before_rank = line[space_index + 7]

        result_moved_file = trans_file3.get(moved_file)
        result_moved = trans_file1.get(moved_rank)
        result_before = trans_file2.get(before_rank)

        if "打" in line:
            piece = USI_PIECES.get(line[space_index + 3])
            made_line = str(piece) + "*" + str(result_moved_file) + str(result_moved) + " "
        else:
            made_line = str(before_file) + str(result_before) + str(result_moved_file) + str(result_moved)

            if "成(" in line:
                made_line += "+ "
            else:
                made_line += " "
                
        result += made_line
    
    return result


# KIF フォルダ内の全ファイルを処理する
def process_all_kif():
    """ KIF フォルダ内の全棋譜を SFEN に変換し、output.sfen に追加 """
    os.makedirs(SFEN_OUTPUT_FOLDER, exist_ok=True)

    kif_files = [f for f in os.listdir(KIFS_FOLDER) if f.endswith(".kif")]

    if not kif_files:
        print("⚠️ KIFフォルダに処理するファイルがありません。")
        return

    with open(SFEN_OUTPUT_FILE, "a", encoding="utf-8") as f:  # 追記モードで開く
        for kif_file in kif_files:
            kif_path = os.path.join(KIFS_FOLDER, kif_file)
            print(f"🔍 処理中: {kif_path}")

            # KIF をクリーニング
            cleaned_moves = clean_kifu(kif_path)

            # SFEN に変換
            if cleaned_moves:
                sfen = process_sfen(cleaned_moves)
                f.write(sfen + "\n")  # `output.sfen` に1行ずつ追加

                print(f"✅ 追加完了: {SFEN_OUTPUT_FILE}")

    print(f"✨ すべての KIF を SFEN に変換し、output.sfen に追加しました！")


# メイン処理
if __name__ == "__main__":
    process_all_kif()
