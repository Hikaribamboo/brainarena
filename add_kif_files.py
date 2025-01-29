import os 
import time

# フォルダパス
KIFS_FOLDER = "kifs"
TRANSLATED_FOLDER = "sfen_maker_1/output_sfens"
SFEN_OUTPUT = os.path.join(TRANSLATED_FOLDER, "output.sfen")

# 1. 棋譜をコマンドプロンプトから入力し、ファイルに保存
def save_kif():
    print("\n📥 棋譜をペーストしてください（終了: Enter 2回 / スクリプト停止: Ctrl+C）:")
    kif_text = []
    
    while True:
        try:
            line = input()
            if line.strip():  # 空行を無視
                kif_text.append(line)
            else:
                break  # 連続で Enter が押されたら終了
        except KeyboardInterrupt:
            print("\n🛑 ユーザーが中断しました。終了します。")
            return None
    
    if not kif_text:
        print("⚠️ 棋譜が入力されませんでした。再入力してください。")
        return None
    
    # 棋譜を新しいファイルとして保存
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    kif_filename = os.path.join(KIFS_FOLDER, f"kif_{timestamp}.kif")
    
    with open(kif_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(kif_text))
    
    print(f"✅ 棋譜を保存しました: {kif_filename}")
    return kif_filename

# メイン処理
def main():
    os.makedirs(KIFS_FOLDER, exist_ok=True)
    os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

    try:
        while True:
            save_kif()  # 棋譜を連続で入力
    except KeyboardInterrupt:
        print("\n🛑 ユーザーが Ctrl+C を押したため、終了します。")

if __name__ == "__main__":
    main()
