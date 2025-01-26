import os
import json
import subprocess
import time
import queue
import threading

# === ユーザー設定 ===
ENGINE_PATH = "C:\\Users\\hikar\\yaneuraou\\YaneuraOu_NNUE-tournament-clang++-avx2.exe"
CONVERTED_FILE = "translated_kifs/output.sfen"
OUTPUT_JSON = "tsumeshogi.json"

MATE_TIME_MS = 5000
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
    """
    go mate コマンドで最善手(multipv=1)と次善手(multipv=2)の
    "score mate x" と詰み手順を取得し、(mate1, mate2, mate_steps) タプルで返す。
    """
    mate_dict = {}
    mate_steps = ""  # 初期化（詰み手順）

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

                    # `multipv=1` の場合に詰み手順を取得
                    if mpv_val == 1 and "pv" in parts:
                        pv_idx = parts.index("pv") + 1
                        mate_steps = " ".join(parts[pv_idx:])  # `pv` 以降の手順を取得
            except ValueError:
                pass

    return mate_dict.get(1), mate_dict.get(2), mate_steps


def get_turn(moves):
    """手番を判定 (先手: 'black', 後手: 'white')"""
    return "black" if len(moves) % 2 == 0 else "white"


def get_evaluation_score(lines):
    """
    エンジン出力から評価値(数値)を取得。
    "score cp XXX" → XXX が評価値
    "score mate XXX" → 詰みなので便宜上 ±100000 * XXX など大きい値にする
    """
    for line in lines:
        if "score cp" in line:
            parts = line.split()
            return int(parts[parts.index("score") + 2])
        elif "score mate -0" in line:
            return int(0)
        elif "score mate" in line:
            parts = line.split()
            # mate X → +なら先手勝ち、-なら後手勝ちだが
            # ここでは便宜上 ±巨大値にしておく
            mate_num = int(parts[parts.index("score") + 2])
            # 符号は出力上ないので、mate_num が正なら先手勝ち扱いに
            # ざっくり eval=+100000 * X としておく
            return mate_num * 100000
    return None

def main():
    if not os.path.exists(CONVERTED_FILE):
        print(f"❌ {CONVERTED_FILE} not found.")
        return

    with open(CONVERTED_FILE, "r", encoding="utf-8") as f:
        line = f.readline().strip()
        if not line.startswith("position startpos moves"):
            print("❌ USI形式の棋譜ではありません。:", line)
            return
        moves = line.split()[3:]  # 先頭の "position startpos moves" を除いた手順リスト

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
    wait_for_mate(out_queue, engine, 5000)
    send_command(engine, f"setoption name MultiPV value {MULTI_PV}")
    send_command(engine, "setoption name USI_Hash value 256")
    send_command(engine, "setoption name USI_OwnBook value false")
    send_command(engine, "isready")
    wait_for_mate(out_queue, engine, 5000)
    print("✅ エンジン初期化完了")

    # 見つかった詰み局面のうち「余詰めなし」を最後に記録しておきたい
    final_record = None

    # === 後ろから局面をチェックするイメージで、
    #     moves を消しながら(ポップしながら)ループ ===
    while moves:
        turn = get_turn(moves)  # 次の手番（black=先手, white=後手）
        print(f"\n🔍 現在の手番: {'▲先手' if turn == 'black' else '△後手'}")

        # いまの局面を設定
        position_cmd = "position startpos moves " + " ".join(moves)
        send_command(engine, position_cmd)

        # まずは shallow な評価値を取得 (go depth 1 など)
        send_command(engine, "go depth 1")
        eval_lines = wait_for_mate(out_queue, engine, 2000)
        eval_score = get_evaluation_score(eval_lines)

        if eval_score is None:
            print("⚠️ 評価値が取得できませんでした。探索停止。")
            break

        elif eval_score == 0:
            print("⏩ 詰みの局面なので1手戻します")
            moves.pop()  # 先手の手
            continue

        elif eval_score < -2000:
            print("⏩ 不利のため1手戻します")
            moves.pop()
            continue

        elif eval_score >= 2000:
            print("🔔詰みチェックを行います")
            print("🔎 詰み探索(go mate)")

            send_command(engine, f"go mate {MATE_TIME_MS}")  # 時間指定
            lines_captured = wait_for_mate(out_queue, engine, MATE_TIME_MS + 1000)

            sfen_str = position_cmd
            mate1, mate2, steps_str = parse_mate_info(lines_captured)
            print(f"   最善手の詰み手数: {mate1}, 次善手の詰み手数: {mate2}")

            # mate1がNone なら詰みなし => ここで詰将棋にできないので終了
            if mate1 is None:
                print("🔔 この局面では詰みなし → これ以上詰将棋は作れないので終了")
                break

            # 余詰め判定: mate1 == mate2 (同手数の別解) があれば即終了
            if mate2 is not None and mate1 == mate2:
                print("⚠️ 余詰め発生（最善手と次善手の手数が同じ）→ 詰将棋として不採用・終了")
                final_record = None  # 余詰めが出た時点で破棄
                break

            else:
                print("⏩ 詰みが見つかり余詰めがないので2手戻します")
                print("⏩⏩⏩",eval_lines[0])
                
                # 記録更新: この局面を「最後に見つかった詰み問題」として記憶
                final_record = {
                    "board": sfen_str,       # SFEN形式
                    "steps": steps_str,      # 答えの指し手
                    "mate_length": mate1,    # 最短詰手数
                }
                
                moves.pop()  # 先手の手
                moves.pop()  # 後手の手
                continue

        else:
            print("✅ 最後の詰み以降の詰みが確認できなかったので問題を保存して終了します")
            break


    # エンジン終了処理
    send_command(engine, "quit")
    reader.stop()
    engine.wait()
    print("✅ エンジン終了")
    
    # 最後に見つかった「詰みあり & 余詰めなし」の局面を JSON に保存
    
    if final_record:
        print(final_record)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(final_record, f, indent=2, ensure_ascii=False)
        print(f"✨ JSON保存完了: {OUTPUT_JSON}")
    else:
        print("⚠️ 最終的に詰将棋を作れる局面が見つかりませんでした。JSON保存なし。")
        
if __name__ == "__main__":
    main()
