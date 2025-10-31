# Team 10

import sys
import random

TARGET_CLEAR = 5  # クリア必要フロア数
TOTAL_FLOORS = 8
DIRECTIONS = {'w': (-1,0), 's': (1,0), 'a': (0, -1), 'd': (0,1)}  # 移動方向
TILE_SYMBOLS = {
    '#': 'Wall',
    '.': 'Path',
    'S': 'Start',
    'G': 'Goal',
    'N': 'Needle_Trap',
    'P': 'Potion',
    'S': 'Sword',
    'T': 'Teleportation'

} 

MAP_DIR_PATH = "map_data/"

class GameState:
    def __init__(self) -> None:
        self.cleared_count = 0
        self.current_floor_index = -1

        self.is_game_over = False  # ゲームオーバーフラグ
        self.is_game_cleared = False  # ゲームクリアフラグ
        
        self.all_floors = [random.sample(range(1, TOTAL_FLOORS + 1), TOTAL_FLOORS)]


class Floor:
    def __init__(self, ) -> None:
        # self.grid = 
        # self.start = 
        # self.goal = 
        pass


class Item:
    def __init__(self) -> None:
        pass

class Weapon(Item):
    def __init__(self) -> None:
        super().__init__()

class Potion(Item):
    def __init__(self) -> None:
        super().__init__()

class Trap(Item):
    def __init__(self) -> None:
        super().__init__()


class Player:
    DEFAULT_HP = 100
    DEFAULT_ATK = 10
    def __init__(self) -> None:
        self.player_hp = Player.DEFAULT_HP
        self.player_attack = Player.DEFAULT_ATK
        pass


class Enemy:
    def __init__(self) -> None:
        self.enemy_hp = 100
        self.enemy_attack = 10
        pass


def read_map_data(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_grid_section = False
    in_info_section = False
    grid = []
    info = {}

    for line in lines:
        line = line.rstrip("\n")
        if line == "[grid]":
            in_grid_section = True
            in_info_section = False
            continue
        elif line == "[info]":
            in_grid_section = False
            in_info_section = True
            continue

        if in_grid_section:
            # グリッドデータの処理
            grid.append(list(line))
        elif in_info_section:
            # 情報データの処理
            tmp = line.split(": ")
            if len(tmp) == 2:
                info[tmp[0]] = 
                continue
    
    return grid, info


def print_grid(grid):
    for row in grid:
        print("".join(row))

# Main ループ
def main():
    print("Main Loop")
    grid, info = read_map_data(MAP_DIR_PATH + "map06.txt")
    print_grid(grid)
    print(info)

if __name__ == "__main__":
    main()