import os
import time
import subprocess

# フォルダパス
KIFS_FOLDER = "kifs"
TRANSLATED_FOLDER = "translated_kifs"
SFEN_OUTPUT = os.path.join(TRANSLATED_FOLDER, "output.sfen")

# 1. 棋譜をコマンドプロンプトから入力し、ファイルに保存
def save_kif():
    print("📥 棋譜をペーストしてください（終了: Ctrl+C）:")
    kif_text = []
    
    while True:
        try:
            line = input()
            if line.strip():  # 空行を無視
                kif_text.append(line)
            else:
                break
        except KeyboardInterrupt:
            break
    
    if not kif_text:
        print("⚠️ 棋譜が入力されませんでした。処理を中断します。")
        return None
    
    # 棋譜を新しいファイルとして保存
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    kif_filename = os.path.join(KIFS_FOLDER, f"kif_{timestamp}.kif")
    
    with open(kif_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(kif_text))
    
    print(f"✅ 棋譜を保存しました: {kif_filename}")
    return kif_filename

# 2. KIF → SFEN 変換
def convert_kifs_to_sfen():
    print("🔄 KIF から SFEN に変換中...")
    subprocess.run(["python", "convert_kif.py"])
    print("✅ 変換完了！")

# 3. SFEN を一行ずつ処理
def process_sfen_lines():
    if not os.path.exists(SFEN_OUTPUT):
        print(f"⚠️ SFENファイルが見つかりません: {SFEN_OUTPUT}")
        return
    
    with open(SFEN_OUTPUT, "r", encoding="utf-8") as f:
        sfen_lines = f.readlines()
    
    if not sfen_lines:
        print("⚠️ SFEN ファイルが空です。処理を中断します。")
        return
    
    print("🔎 SFEN の処理を開始...")
    
    for i, sfen in enumerate(sfen_lines):
        sfen = sfen.strip()
        if not sfen:
            continue
        
        print(f"\n🎯 [{i+1}/{len(sfen_lines)}] SFEN を処理中: {sfen}")
        
        # tsume_maker.py に SFEN を渡して処理
        subprocess.run(["python", "tsume_maker.py", sfen])
    
    print("✅ すべての SFEN の処理が完了しました！")

# メイン処理
def main():
    os.makedirs(KIFS_FOLDER, exist_ok=True)
    os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

    kif_file = save_kif()
    if kif_file:
        convert_kifs_to_sfen()
        process_sfen_lines()

if __name__ == "__main__":
    main()
