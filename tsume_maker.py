import os
import json
import subprocess
import time
import queue
import threading

# === ユーザー設定 ===
ENGINE_PATH = "C:\\Users\\hikar\\yaneuraou\\YaneuraOu_NNUE-tournament-clang++-avx2.exe"
CONVERTED_FILE = "C:\\Users\\hikar\\program_develop\\aoto-tsumeshogi-question\\aoto-tsumeshogi-question\\sfen_maker_1\\output_sfens\\output.sfen"


MATE_TIME_MS = 3000
MULTI_PV = 2

def send_command(engine, cmd):
    """エンジンにコマンドを送る"""
    if engine.poll() is not None:
        return
    print(f"📝 コマンド送信: {cmd}")
    engine.stdin.write(cmd + "\n")
    engine.stdin.flush()

class OutputReader(threading.Thread):
    """エンジンの出力を並列で読むスレッド"""
    def __init__(self, engine, out_queue):
        super().__init__()
        self.engine = engine
        self.out_queue = out_queue
        self.running = True

    def run(self):
        while self.running:
            line = self.engine.stdout.readline()
            if not line:
                if self.engine.poll() is not None:
                    break
                time.sleep(0.01)
                continue
            self.out_queue.put(line.strip())

    def stop(self):
        self.running = False

def wait_for_mate(out_queue, engine, timeout_ms):
    """詰み探索や通常探索の応答を待つ"""
    start_time = time.time()
    lines = []

    while True:
        if engine.poll() is not None:
            print("⚠️ エンジンが終了しています。")
            break

        elapsed = (time.time() - start_time) * 1000
        if elapsed > timeout_ms:
            print("⏳ 探索時間超過！強制停止")
            send_command(engine, "stop")
            time.sleep(1)
            break

        try:
            line = out_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        print("🔹", line)
        lines.append(line)

    return lines

def parse_mate_info(lines):
    """詰み情報を解析し、詰み手数と手順を取得"""
    mate_dict = {}
    mate_steps = ""

    for line in lines:
        if "info" in line and "multipv" in line and "score mate" in line:
            parts = line.split()
            try:
                mpv_idx = parts.index("multipv")
                mpv_val = int(parts[mpv_idx + 1])  # 1 or 2
                score_idx = parts.index("score")
                if parts[score_idx + 1] == "mate":
                    mate_val = int(parts[score_idx + 2])
                    mate_dict[mpv_val] = mate_val

                    if mpv_val == 1 and "pv" in parts:
                        pv_idx = parts.index("pv") + 1
                        mate_steps = " ".join(parts[pv_idx:])
            except ValueError:
                pass

    return mate_dict.get(1), mate_dict.get(2), mate_steps

def main():
    if not os.path.exists(CONVERTED_FILE):
        print(f"⚠️ {CONVERTED_FILE} が見つかりません。スクリプトを終了します。")
        return  # スクリプトを停止

    engine_dir = os.path.dirname(ENGINE_PATH)
    if engine_dir:
        os.chdir(engine_dir)

    engine = subprocess.Popen(
        [ENGINE_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    out_queue = queue.Queue()
    reader = OutputReader(engine, out_queue)
    reader.start()

    # --- エンジン初期化 ---
    send_command(engine, "usi")
    send_command(engine, f"setoption name MultiPV value {MULTI_PV}")
    send_command(engine, "setoption name USI_Hash value 256")
    send_command(engine, "setoption name USI_OwnBook value false")
    send_command(engine, "isready")
    print("✅ エンジン初期化完了")

    # === SFENリストを一行ずつ処理 ===
    with open(CONVERTED_FILE, "r", encoding="utf-8") as f:
        sfen_list = f.readlines()

    if not sfen_list:
        print("⚠️ SFENが空です。処理を終了します。")
        return

    # JSONファイルのパス
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_JSON = os.path.join(SCRIPT_DIR, "tsumeshogi.json")

    # 既存のJSONファイルを読み込む（なければ空リスト）
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    for sfen in sfen_list:
        sfen = sfen.strip()
        if not sfen.startswith("position startpos moves"):
            print(f"⚠️ 無効なSFEN: {sfen}")
            continue

        print(f"\n🔍 処理中の局面: {sfen}")

        # エンジンに局面をセット
        send_command(engine, sfen)

        # 詰みチェック
        send_command(engine, f"go mate {MATE_TIME_MS}")
        lines_captured = wait_for_mate(out_queue, engine, MATE_TIME_MS + 1000)

        mate1, mate2, steps_str = parse_mate_info(lines_captured)
        print(f"   最善手の詰み手数: {mate1}, 次善手の詰み手数: {mate2}")

        if mate1 is None:
            print("🔔 この局面では詰みなし → スキップ")
            continue

        if mate2 is not None and mate1 == mate2:
            print("⚠️ 余詰め発生 → スキップ")
            continue

        # 記録更新
        final_record = {
            "board": sfen,
            "steps": steps_str,
            "mate_length": mate1,
        }
        existing_data.append(final_record)

        print(f"📜 保存データ: {json.dumps(final_record, indent=2, ensure_ascii=False)}")

    # JSONファイルに保存
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        print(f"✨ JSON保存完了: {OUTPUT_JSON}")
    except Exception as e:
        print(f"❌ JSON保存エラー: {e}")

    # エンジン終了処理
    send_command(engine, "quit")
    reader.stop()
    engine.wait()
    print("✅ エンジン終了")

if __name__ == "__main__":
    main()

