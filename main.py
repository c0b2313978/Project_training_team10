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

MAP_DATA_PATH = "map_data/"

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




# Main ループ
def main():
    print("Main Loop")
    pass



if __name__ == "__main__":
    main()