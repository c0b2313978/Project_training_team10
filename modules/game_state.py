from modules.floor import Floor
from modules.player import Player
from modules.constants import MAP_DIR_PATH, TARGET_CLEAR, TOTAL_FLOORS, DIRECTIONS
import random

class GameState:
    def __init__(self, requires_map_file_path: list[str] = []) -> None:
        self.is_game_state = True  # ゲーム進行中フラグ

        self.requires_map_file_path = requires_map_file_path
        if self.requires_map_file_path:  # デバッグ用：特定フロア指定
            global TARGET_CLEAR
            TARGET_CLEAR = len(self.requires_map_file_path)  # デバッグ用：クリア必要フロア数
            self.all_floors = self.requires_map_file_path  # デバッグ用：特定フロア指定
        else:
            self.all_floors = random.sample(list(range(1, TOTAL_FLOORS + 1)), TARGET_CLEAR)  # クリア必要フロアリスト
            # self.all_floors = list(range(1, TOTAL_FLOORS + 1))  # デバッグ用：全フロアクリア
            self.all_floors.append(0)  #  強制的にmap00を追加
            TARGET_CLEAR+=1
            print(f"Selected Floors to Clear: {self.all_floors}")  # デバッグ用表示

        self.cleared_count = 0  # クリア済みフロア数
        self.current_floor_index = 0  # 現在のフロアインデックス

        self.is_game_over = False  # ゲームオーバーフラグ
        self.is_game_cleared = False  # ゲームクリアフラグ

        self.floor: 'Floor' = self.start_floor()  # 現在のフロアインスタンス
        print_all_opening()
        print("正常にフロアが開始されました。")  # デバッグ用表示
        self.player: 'Player' = Player(self.floor.start)  # プレイヤーインスタンス
        print() #マップごとのルール説明
        print(self.floor.rule)

    # ====== ゲーム進行管理 ======
    def game_state(self) -> bool:
        """ ゲーム進行中かどうかを返す """
        self.is_game_state = not (self.is_game_over or self.is_game_cleared)
        return self.is_game_state

    def start_floor(self) -> 'Floor':
        """ 現在のフロアを開始する """
        floor_id = str(self.all_floors[self.current_floor_index])  # 現在のフロアID
        
        if self.requires_map_file_path:  # デバッグ用：特定フロア指定
            map_file_path = self.requires_map_file_path[self.current_floor_index]
        else:
            map_file_path = MAP_DIR_PATH + f"map0{floor_id}.txt"  # マップファイルパス
        floor = Floor(map_file_path, floor_id=floor_id)  # フロアインスタンス生成
        return floor

    def next_floor(self, player: Player) -> None:
        """ フロアクリア後に呼ぶ。{TARGET_CLEAR}回クリアでゲームクリア """
        self.cleared_count += 1
        self.current_floor_index += 1
        player.floor_clear_keys_reset() # 鍵リセット

        if self.cleared_count >= TARGET_CLEAR:
            self.is_game_cleared = True
            # print("おめでとうございます！すべてのフロアをクリアしました！")
        else:
            print(f"フロアクリア！ 残り {TARGET_CLEAR - self.cleared_count} 層です。")
    
    def check_game_over(self) -> bool:
        """ ゲームオーバー判定 """
        if self.player.hp <= 0:
            self.is_game_over = True
            print("あなたは力尽きました。ゲームオーバーです。")
            return True
        return False

    def check_game_cleared(self) -> bool:
        """ ゲームクリア判定 """
        if self.is_game_cleared:
            print("\n\n\n")
            print_game_text("game_texts/Ending.txt")
            # print("おめでとうございます！すべてのフロアをクリアしました！")
            return True
        return False


    # ===== 入出力 =====
    def read_command(self) -> str:
        """ プレイヤーからのコマンド入力を受け取る """
        while True:
            command = input("(w/a/s/d 移動, u:ポーション, q:終了) > ").strip().lower()
            if command in ['w', 'a', 's', 'd', 'u', 'q']:
                return command
            # print("不正ななコマンドです。{w, a, s, d, u, q} のいずれかを入力してください。")

    # ===== ゲーム状態更新 ======
    def step_turn(self, command = "") -> None:
        """ 1ターン（プレイヤー入力 -> セルイベント -> 敵行動 -> 判定） """
        self.floor.print_grid(self.player)
        print()
        self.player.print_status()
        print()

        if not command in ['w', 'a', 's', 'd', 'u', 'q']:
            command = self.read_command()  # コマンド入力

        if command == 'q':
            print("ゲーム終了します。")
            self.is_game_over = True
            return

        elif command == 'u':
            self.player.use_potion()  # ポーション使用
            return
        
        new_position = try_move_player(self.player, command, self.floor.grid)
        if new_position is not None:
            self.player.position = new_position
            self.player.last_move_direction = command
        else:
            print("その方向には移動できません！")
            return
        
        # セルに入った際のイベント処理
        self.floor.enter_cell(self.player)

        # モンスター行動
        occupied = {m.pos for m in self.floor.monsters.values() if m.alive}
        for monster in self.floor.monsters.values():
            if not monster.alive:
                continue
            if monster.increment_turn():  # move_every に達したら移動
                # monster.pos
                new_pos = monster.monster_next_move(self.player.position, self.floor.grid, occupied_positions=occupied)
                if new_pos in occupied:
                    continue  # 移動先が他のモンスターと被る場合は移動しない
                occupied.remove(monster.pos)
                occupied.add(new_pos)
                monster.pos = new_pos
                
                # occupied.remove(monster.pos)
                # occupied.add(monster.pos)

        # モンスターとの衝突判定
        for monster in self.floor.monsters.values():
            if not monster.alive:
                continue
            if monster.pos == self.player.position:
                print(f"モンスター {monster.id} と遭遇しました！戦闘開始！  - game_state.py - step_turn()")
                self.floor.battle_monster(self.player, monster)

        # ゴール判定
        is_goal, goal_message = self.floor.check_goal(self.player)
        if is_goal:
            print("ゴールに到達しました！フロアクリア！")
            # print(goal_message)
            self.next_floor(self.player)  # フロアクリア処理
            if not self.is_game_cleared:
                self.floor = self.start_floor()
                self.player.position = self.floor.start
                print() #マップごとのルール説明
                print(self.floor.rule)
            else:
                self.check_game_cleared()  #この関数が発生しないbugを直した
            return
        else:
            if goal_message:
                print(goal_message)

        self.check_game_over()
        self.check_game_cleared()
    

# ==================== 便利関数群 ====================

#ファイル読み、文字出力
def print_game_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(text)

def print_all_opening():
    arry = ["game_texts/Firstgame_ui.txt","game_texts/Opening.txt","game_texts/Basic_rule.txt","game_texts/Controls_guide.txt"]
    for i in arry:
        with open(i, 'r', encoding='utf-8') as f:
            text = f.read()
        print(text)
        input("")

# プレイヤーからのコマンド入力を受け取る
def read_player_command() -> str:
    while True:
        command = input("(w/a/s/d 移動, u:ポーション, q:終了) > ").strip().lower()
        if command in ['w', 'a', 's', 'd', 'u', 'q']:
            return command
        print("不正ななコマンドです。{w, a, s, d, u, q} のいずれかを入力してください。")
        # print("Invalid command! Please enter w, a, s, d, u, or q.")


# 移動可能か判定し、可能なら移動先の座標を返す
def try_move_player(player: Player, direction: str, grid: list[list[str]]) -> tuple[int, int] | None:
    """ プレイヤーを direction に移動させる。移動可能なら新しい座標を、不可なら None を返す """
    n, m = len(grid), len(grid[0])
    delta_row, delta_col = DIRECTIONS[direction]
    new_row = player.position[0] + delta_row
    new_col = player.position[1] + delta_col

    # 範囲内チェック
    if not(0 <= new_row < n and 0 <= new_col < m):
        # print("Out of bounds!")
        return None

    # 壁チェック
    if grid[new_row][new_col] != '.':
        # print("Hit a wall!")
        return None

    return (new_row, new_col)
