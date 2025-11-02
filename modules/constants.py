# ==================== ゲーム設定 ====================

TARGET_CLEAR = 5  # クリア必要フロア数
TOTAL_FLOORS = 8  # 有効な総フロア数
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

sample_map_data = MAP_DIR_PATH + "sample01.txt"