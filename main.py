# Team 10 C0B23139 森山悠太
"""
自作AIの行動決定ロジックは modules/self_made_AI.py の ModeBasedAI クラス内に実装されています．ロジックの詳細な説明は modules/self_made_AI.py の冒頭コメントをご参照ください．

実行方法:
if __name__ == "__main__": ブロック内で以下のいずれかを呼び出してください:
- 自動プレイ: main(auto_play=True)
- 手動プレイ: main(auto_play=False)
- AIの性能評価: performance_evaluation(times=試行回数, agent_class=ModeBasedAI, file_output=True)

## メインループの構造
1. main.py の main 関数内で GameState インスタンスを生成
    GameState: ゲームの状態管理クラス． プレイヤー，フロア，アイテム，モンスター等の情報を保持し，ゲーム進行を制御する．
2. ループの実行
    game_state.game_state() が True である限り継続
3. 情報の取得
    game_state.get_known_info() を呼び出し，プレイヤーが知り得る情報を取得
        info: 現在のフロア情報，プレイヤー情報，アイテム情報，モンスター情報などを含む辞書
        legal_actions: 現在の状況で可能な行動コマンドのリスト
4. AIの行動決定
    ModeBasedAI インスタンスの decide_move メソッドに情報を渡し，次の行動コマンドを決定
5. ターンの進行
    game_state.step_turn(command) を呼び出し，決定したコマンドに基づいて，プレイヤーの移動，イベント処理，モンスターの行動などを処理


## GameState.get_known_info() から取得できる情報 (info, legal_actions) (modules/game_state.py line:188 ~ 244)
AIに渡される info 辞書は以下の構造を持つ:
- 'player':
    - 'position': 現在の座標 (row, col)
    - 'hp': 現在の体力
    - 'attack': 現在の攻撃力 (武器込み)
    - 'keys': 所持している鍵のIDリスト
    - 'potions': 所持しているポーションのIDリスト
    - 'equipped_weapon_id': 装備中の武器ID
    - 'equipped_weapon_attack': 装備中の武器の攻撃力
- 'floor':
    - 'id': フロアID
    - 'grid': マップの2次元リスト ('#'=壁, '.'=通路)
    - 'visible_items': 見えているアイテムのリスト (id, pos, type)
    - 'hidden_items': '?'で表示される隠しアイテムの位置リスト
    - 'monsters': 生存しているモンスターのリスト (id, pos, strength)
    - 'gimmicks': 氷床やダメージ床の位置情報
    - 'doors': ドアの位置と開閉状態
    - 'chests': チェストの位置と開閉状態
    - 'teleports': テレポートマスの座標集合（リンク関係は不明、位置のみ）
    - 'goal': ゴールの座標リスト

legal_actions は現在可能な行動コマンドのリスト:
- 'w', 'a', 's', 'd': 移動コマンド
- 'u': ポーション使用コマンド (所持時)


## ModeBasedAI decide_move メソッドのインターフェース
- 引数:
    - info: GameState.get_known_info() から取得した情報辞書
    - legal_actions: 現在可能な行動コマンドのリスト
- 戻り値:
    - command (str): 'w', 'a', 's', 'd' (移動) または 'u' (ポーション使用)

- ロジック概要:
    1. モード制御で目的地を切り替える:
        - USE_POTION(HP低下かつ所持時) -> WEAPON_SEARCH -> POTION_SEARCH -> KEY_SEARCH -> HIDDEN_ITEM_SEARCH -> MONSTER_HUNT -> GOAL_SEARCH の順で優先度を判断．
    2. モードに応じて floor 情報からターゲット集合を構成し，ダイクストラ法で「最小コスト経路の最初の一手」を選ぶ． 経路が無効なら合法手からランダム選択．
        - 移動コストは「基本移動 + 罠 + 地形ダメージ + 戦闘ダメージ」を加算． 勝てないモンスターは INF (通行不可) として扱う．
    3. 氷床(ice)は滑り移動をシミュレーションし，滑走中のセルにあるアイテムも回収対象として扱う．
    4. teleport は floor 変更時に初期化し，前ターン行動から対応先を推定・確定して経験的に teleport_map を更新する．

"""
import os
from random import seed
from modules.game_state import GameState
from modules.self_made_AI import RandomAI, ModeBasedAI

# seed(0)

# Main ループ
def main(auto_play=False, agent_class=ModeBasedAI, file_output = False):
    output_file_path = "game_log.txt"
    output_file_object = open(output_file_path, mode='w', encoding='utf-8') if file_output else None
    
    game_state = GameState(output_file_object=output_file_object)
    agent = agent_class(output_file_object=output_file_object)
    
    try:
        while game_state.game_state():
            if auto_play:
                info, legal_actions = game_state.get_known_info()
                command = agent.decide_move(info, legal_actions, output_debug=True)
                game_state.step_turn(command)
                input()  # 一時停止（手動操作時用）
            else:
                game_state.step_turn()
    finally:
        if output_file_object:
            output_file_object.close()


# AIの性能評価確認用
def performance_evaluation(times = 100, agent_class = ModeBasedAI, file_output = True):
    win_count = 0
    output_file_directory = "logs"
    if file_output and not os.path.exists(output_file_directory):
        os.makedirs(output_file_directory)
    
    for i in range(times):
        print(f"=== 試行回数: {i+1} / {times} ===")
        output_file_path = f"{output_file_directory}/attempt_{i+1:03d}.txt"
        output_file_object = open(output_file_path, mode='w', encoding='utf-8') if file_output else None

        game_state = GameState(output_file_object=output_file_object)
        agent = agent_class(output_file_object=output_file_object)
        
        try:
            while game_state.game_state():
                info, legal_actions = game_state.get_known_info()
                command = agent.decide_move(info, legal_actions, output_debug=True)
                game_state.step_turn(command)
            
            if game_state.is_game_cleared:
                win_count += 1
                print("ゲームクリア")
            else:
                print("ゲームオーバー")
            print(f"現在の勝率: {win_count}/{i+1} ({win_count / (i+1) * 100:.2f}%)\n")
        finally:
            if output_file_object:
                output_file_object.close()

    print(f"=== 最終結果 {win_count}/{times} ({win_count / times * 100:.2f}%) ===")


full_maps = [f"map_data/map{file_name:02d}.txt" for file_name in range(1, 9)]
easy_maps = [f"map_data/map{file_name:02d}.txt" for file_name in (1, 2, 3, 5, 6)]
def tmp(auto_play=False):
    # game_state = GameState(requires_map_file_path=easy_maps)  # デバッグ用：特定フロア指定
    game_state = GameState(requires_map_file_path=["map_data/map06.txt"])  # デバッグ用：特定フロア指定
    agent = ModeBasedAI()
    
    while game_state.game_state():
        if auto_play:
            info, legal_actions = game_state.get_known_info()
            command = agent.decide_move(info, legal_actions, output_debug=True)
            game_state.step_turn(command)
            input()  # 一時停止（手動操作時用）
        else:
            game_state.step_turn()


if __name__ == "__main__":
    # main(auto_play=True)
    # tmp(auto_play=True)
    # tmp(auto_play=False)
    performance_evaluation(times=100, agent_class=ModeBasedAI, file_output=True)
