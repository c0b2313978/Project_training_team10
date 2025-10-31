# Team 10

import sys
import random
import time

TARGET_CLEAR = 5  # クリア必要フロア数
TOTAL_FLOORS = 8
DIRECTIONS = {'w': (-1,0), 's': (1,0), 'a': (0, -1), 'd': (0,1)}  # 移動方向
TILE_SYMBOLS = {
    '#': 'Wall',
    '.': 'Path',
    'S': 'Start',
    'G': 'Goal',
    'M': 'Monster',
    'N': 'Needle_Trap',
    'P': 'Potion',
    'W': 'Weapon',
    'T': 'Teleportation'
    
} 

MAP_DIR_PATH = "map_data/"
TEXT_DIR_PATH = "game_texts/"

class GameState:
    def __init__(self) -> None:
        self.cleared_count = 0
        self.current_floor_index = -1

        self.is_game_over = False  # ゲームオーバーフラグ
        self.is_game_cleared = False  # ゲームクリアフラグ
        
        self.all_floors = [random.sample(range(1, TOTAL_FLOORS + 1), TOTAL_FLOORS)]


class Floor:
    def __init__(self, floor_index) -> None:
        self.floor_index = floor_index
        self.grid, self.info = read_map_data(MAP_DIR_PATH + f"map0{floor_index}.txt") 
        # self.start = 
        # self.goal = 
        pass


class Item:
    def __init__(self, id_, type_, pos, hidden=False, params=None):
        self.id = id_
        self.type = type_        # 'weapon'|'potion'|'key'|'trap'
        self.pos = pos
        self.hidden = hidden
        self.params = params or {}
        self.picked = False
        self.one_time_used = False  # trap用


class Door:
    def __init__(self, id_, pos, requires_key=None):
        self.id = id_
        self.pos = pos
        self.requires_key = requires_key  # 'red' など
        self.locked = True

class Chest:
    def __init__(self, id_, pos, requires_key=None, contents=None):
        self.id = id_
        self.pos = pos
        self.requires_key = requires_key
        self.contents = contents or []  # item_id or 'gen:weapon:+3'
        self.opened = False

class Teleport:
    def __init__(self, id_, src, dst, bidirectional=False):
        self.id = id_
        self.src = src
        self.dst = dst
        self.bidirectional = bidirectional

# class Weapon(Item):
#     def __init__(self) -> None:
#         super().__init__()

# class Potion(Item):
#     def __init__(self) -> None:
#         super().__init__()

# class Trap(Item):
#     def __init__(self) -> None:
#         super().__init__()

class Monster:
    def __init__(self, id_, pos, ai_type, ai_params, move_every=1, drop_list=None):
        self.id = id_
        self.pos = pos
        self.ai_type = ai_type      # 'static'|'random'|'chase'|'patrol'
        self.ai_params = ai_params or {}
        self.move_every = move_every
        self.turn_counter = 0
        self.alive = True
        self.drop_list = drop_list or []
        # ステータスはフロア侵入時に自動で設定（要件）


class Gimmicks:
    def __init__(self):
        self.ice_regions = []      # list of sets/rects → 下でセル集合化
        self.ice_cells = set()     # 実体（セル集合）
        self.slide_triggers_each_cell = True
        self.hp_drain_per_step = 0
        self.monster_can_enter_ice = True
        self.trap_cells = set()    # 地形的罠セル（ダメ10など簡易）


class Player:
    MAX_HP = 100
    BASE_ATK = 10
    def __init__(self, start) -> None:
        self.hp = Player.MAX_HP
        self.attack = Player.BASE_ATK
        self.position = start  # (row, col)
        self.keys = set()
        self.inventory = {}  # id -> Item


class Enemy:
    def __init__(self) -> None:
        self.enemy_hp = 100
        self.enemy_attack = 10
        pass


#ランダムにマップを選択しリストにまとめ
def random_select_map():
    # map01 ~ map08 のリストを作成
    maps = [f"map{str(i).zfill(2)}.txt" for i in range(1, 9)]
    
    # ランダムに5つ選ぶ（重複なし）
    selected_maps = random.sample(maps, 5)
    
    return selected_maps


#ファイル読み、文字出力
def print_game_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(text)


def read_map_data(file_path: str) -> tuple[list[list[str]], dict[str, tuple[int, int]]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    buckets = {
        'grid':[], 'info':[], 'items':[], 
        'monsters':[], 'doors':[], 'chests':[], 
        'teleports':[], 'goal':[], 'gimmicks':[], 'rule':[]}

    in_grid_section = False
    in_info_section = False
    in_rule_section = False
    grid = []
    info = {}

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue

        if line == "[grid]":
            in_grid_section = True
            in_info_section = False
            in_rule_section = False
            continue
        elif line == "[info]":
            in_grid_section = False
            in_info_section = True
            in_rule_section = False
            continue
        elif line == "[rule]":
            in_grid_section = False
            in_info_section = False
            in_rule_section = True
            continue

        if in_grid_section:
            # グリッドデータの処理
            grid.append(list(line))
            continue

        elif in_info_section:
            # print(line)
            # 情報データの処理
            tmp = line.split(": ")
            if len(tmp) == 2:
                info[tmp[0]] = tuple(map(int, tmp[1].split(", ")))
                continue
        elif in_rule_section:
            # ルールデータの処理（現状未使用）
            continue

    
    return grid, info


def print_grid(grid, info, player: Player = None):
    for i in range(len(grid)):
        row = []
        for j in range(len(grid[i])):
            if player is not None and (i, j) == player.position:
                row.append('@')
            elif (i, j) == info.get('start'):
                row.append('S')
            elif (i, j) == info.get('goal'):
                row.append('G')
            elif grid[i][j] == '.':
                row.append(' ')
            else:
                row.append(grid[i][j])

        print("".join(row))


def read_player_command() -> str:
    while True:
        command = input("Enter command (w/a/s/d to move, q to quit): ")
        command = command.lower()
        if command in ['w', 'a', 's', 'd', 'q']:
            break
        print("Invalid command! Please enter w, a, s, d, or q.")
    return command


# 移動可能か判定し、可能なら移動先の座標を返す
def try_move_player(player: Player, direction: str, grid: list[list[str]]) -> tuple[int, int]:
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


# ゲーム実行の仮関数
def tmp_run_game():
    # print_game_text(TEXT_DIR_PATH+"Firstgame_ui.txt")
    # time.sleep(1)
    # print_game_text(TEXT_DIR_PATH+"Basic_rule.txt")
    # time.sleep(1)
    # print_game_text(TEXT_DIR_PATH+"Opening.txt")
    # time.sleep(1)
    grid, info = read_map_data(MAP_DIR_PATH + "map08.txt")
    # print(info)
    # return
    player = Player(start=info['start'])

    print_grid(grid, info, player)

    while True:
        command = read_player_command()
        if command == 'q':
            print("Quitting the game.")
            break

        new_position = try_move_player(player, command, grid)
        if new_position is not None:
            player.position = new_position
        else:
            print("Cannot move in that direction!")
        
        if player.position == info['goal']:
            print("Reached the goal!")
            break

        print_grid(grid, info, player)


# Main ループ
def main():
    print_game_text(TEXT_DIR_PATH+"Firstgame_ui.txt")
    time.sleep(1)
    print_game_text(TEXT_DIR_PATH+"Basic_rule.txt")
    time.sleep(1)
    print_game_text(TEXT_DIR_PATH+"Opening.txt")
    time.sleep(1)
    for i in range(5):
        palying_map = random_select_map()
        grid, info = read_map_data(MAP_DIR_PATH + palying_map[i])
        # print(info)
        # return
        player = Player(start=info['start'])

        print_grid(grid, info, player)

        while True:
            command = read_player_command()
            if command == 'q':
                print("Quitting the game.")
                break

            new_position = try_move_player(player, command, grid)
            if new_position is not None:
                player.position = new_position
            else:
                print("Cannot move in that direction!")
            
            if player.position == info['goal']:
                print("Reached the goal!")
                break

            print_grid(grid, info, player)

if __name__ == "__main__":
    main()
    #tmp_run_game()