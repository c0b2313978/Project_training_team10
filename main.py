# Team 10
from pprint import pprint
import json
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

# マップを表示する際のシンボル定義
ENTITY_SYMBOLS = {
    "item": {"weapon": "W", "potion": "P", "key": "K", "trap": "!"},
    "monster": "M",
    "door": lambda door: "/" if door.opened else "D",
    "chest": lambda chest: "C" if not chest.opened else "c",
    "teleport": lambda tp: "T",
    "hidden_item": "?",
}

MAP_DIR_PATH = "map_data/"
TEXT_DIR_PATH = "game_texts/"

sample_map_data = MAP_DIR_PATH + "sample01.txt"

class GameState:
    def __init__(self) -> None:
        self.cleared_count = 0
        self.current_floor_index = -1

        self.is_game_over = False  # ゲームオーバーフラグ
        self.is_game_cleared = False  # ゲームクリアフラグ
        
        self.all_floors = [random.sample(range(1, TOTAL_FLOORS + 1), TOTAL_FLOORS)]


class Floor:
    """
    map_txt から読み込んだ1フロア分の全データ（grid以外はJSONから供給）
    以下はJSONで与える:
        name, reveal_hidden, start, goal, goal.type/keys
        items, monsters, doors, chests, teleports, gimmicks
    """
    def __init__(self, map_file_path: str, specific_json_path: str = "", floor_id: int = -1) -> None:
        self.floor_id = floor_id  # フロアID（任意指定）

        # ===== マップ読み込み =====
        self.grid, self.json_path = read_map_data(map_file_path)
        self.map_size = (len(self.grid), len(self.grid[0]))  # (n_rows, n_cols)
        self.movable_cells = set()  # 通行可能セル集合
        for i in range(self.map_size[0]):
            for j in range(self.map_size[1]):
                if self.grid[i][j] == '.':
                    self.movable_cells.add((i, j))

        # ===== JSONデータ読み込み =====
        if specific_json_path or self.json_path:
            self.info = self._read_json_data(specific_json_path or self.json_path)  # specific_json_path が優先
        else:
            raise ValueError("JSONデータのパスが指定されていません。")

        self.name = self.info.get('name', f"Floor {floor_id}")  # フロア名
        self.reveal_hidden = self.info.get('reveal_hidden', False)  # 隠しアイテム自動発見
        self.start: tuple[int, int] = tuple(self.info['start'])  # 開始位置 (row, col)

        # ===== ゴール =====
        self.goal = {}
        self._goal_init()

        # ===== アイテム =====
        self.items: dict[str, Item] = {}
        self._items_init()

        # ===== モンスター =====
        self.monsters: dict[str, Monster] = {}
        self._monsters_init()

        # ===== ドア =====
        self.doors: dict[str, Door] = {}
        self._doors_init()

        # ===== チェスト =====
        self.chests: dict[str, Chest] = {}
        self._chests_init()

        # ===== テレポート =====
        self.teleports: dict[str, Teleport] = {}
        self._teleports_init()

        # ===== ギミック =====
        # TODO: ギミック初期化

    def _read_json_data(self, json_path: str) -> dict:
        """ JSONデータを読み込み、辞書で返す。 """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    # ===== ゴール情報初期化 =====
    def _goal_init(self):  # TODO: key_only未対応
        goal = self.info.get('goal', {})

        # ゴール方法のタイプ. "reach" | "keys_only" | "reach_and_keys"
        self.goal['type'] = goal.get('type', 'reach')

        # 複数のゴール. trueの場合 pos が2次元リストで渡される
        self.goal['multiple'] = goal.get('multiple', False)  

        # ゴールの位置. type=reach または reach_and_keys で使用
        if self.goal['multiple'] is False:
            self.goal['pos'] = set([tuple(goal.get('pos', (0, 0)))])
        else:
            self.goal['pos'] = set(tuple(p) for p in goal.get('pos', []))
        
        # ゴールに必要なkeyのid. type=keys_only または reach_and_keys で使用
        self.goal['keys'] = list(goal.get('keys', []))

    # ===== アイテム情報初期化 =====
    def _items_init(self):
        items_data = self.info.get('items', [])
        for item_data in items_data:
            item = Item.create_item(**item_data)
            self.items[item.id] = item
    
    # ===== モンスター情報初期化 =====
    def _monsters_init(self):
        monsters_data = self.info.get('monsters', [])
        for monster_data in monsters_data:
            monster = Monster(**monster_data)
            self.monsters[monster.id] = monster
    
    # ===== ドア情報初期化 =====
    def _doors_init(self):
        doors_data = self.info.get('doors', [])
        for door_data in doors_data:
            door = Door(**door_data)
            self.doors[door.id] = door

    # ===== チェスト情報初期化 =====
    def _chests_init(self):
        chests_data = self.info.get('chests', [])
        for chest_data in chests_data:
            chest = Chest(**chest_data)
            self.chests[chest.id] = chest
        
    # ===== テレポート情報初期化 =====
    def _teleports_init(self):  
        teleports_data = self.info.get('teleports', [])
        for teleport_data in teleports_data:
            teleport = Teleport(**teleport_data)
            self.teleports[teleport.id] = teleport

    def print_info(self):
        """ フロア情報を表示する（デバッグ用） """
        print(f"Floor Name: {self.name}")
        print(f"Map Size: {self.map_size}")
        print(f"Start Position: {self.start}")

        print("Goal Info:")
        pprint(self.goal)

        print("Items:")
        pprint(self.items)
        
        print("Monsters:")
        pprint(self.monsters)

        print("Doors:")
        pprint(self.doors)

        print("Chests:")
        pprint(self.chests)

        print("Teleports:")
        pprint(self.teleports)

    # ===== マップ上のシンボル収集 =====
    def _collect_entity_symbols(self) -> dict[tuple[int, int], str]:
        symbols: dict[tuple[int, int], str]= {}
        # items
        for item in self.items.values():
            if item.picked:  # 回収済みアイテム
                continue
            if item.hidden and self.reveal_hidden:  # 未発見の隠しアイテム
                symbols[item.pos] = ENTITY_SYMBOLS["hidden_item"]
            else:
                # symbols[item.pos] = ENTITY_SYMBOLS["item"].get(item.type, "~")
                symbols[tuple(item.pos)] = ENTITY_SYMBOLS["item"].get(item.type, "~")
        
        # monsters
        for monster in self.monsters.values():
            if monster.alive:
                symbols[monster.pos] = ENTITY_SYMBOLS["monster"]
        
        # doors
        for door in self.doors.values():
            symbols[door.pos] = ENTITY_SYMBOLS["door"](door)
        
        # chests
        for chest in self.chests.values():
            symbols[chest.pos] = ENTITY_SYMBOLS["chest"](chest)
        
        # teleports
        for tp in self.teleports.values():
            symbols[tp.source] = ENTITY_SYMBOLS["teleport"](tp)
            if tp.bidirectional:
                symbols[tp.target] = ENTITY_SYMBOLS["teleport"](tp)
        return symbols


    def print_grid(self, player: 'Player' = None):
        """マップ全体を表示する"""
        entity_symbols = self._collect_entity_symbols()

        for i in range(self.map_size[0]):
            row = []
            for j in range(self.map_size[1]):
                pos = (i, j)
                if player is not None and pos == player.position:  # プレイヤー位置
                    row.append('@')
                elif pos == self.start:  # スタート位置
                    row.append('S')  # TODO: もしかしたらいらないかも？
                elif pos in self.goal['pos']:  # ゴール位置
                    row.append('G')
                elif pos in entity_symbols:  # アイテム・モンスター・ギミック
                    row.append(entity_symbols[pos])
                elif self.grid[i][j] == '.':  # 通路
                    row.append(' ')
                else:
                    row.append(self.grid[i][j])  # 壁

            print("".join(row))


# ==================== アイテムクラス群 ====================
class Item:
    def __init__(self, id, type, pos, hidden=False, params=None):
        self.id = id                # 一意なID
        self.type = type            # 'weapon'|'potion'|'key'|'trap'
        self.pos = tuple(pos)              # (row, col)
        self.hidden = hidden        # 描画する際に隠れているかどうか
        self.params = params or {}  # 追加パラメータ辞書
        self.picked = False         # 回収済みかどうか
    
    def __repr__(self):
        return f"Item(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

    @classmethod
    def create_item(cls, id, type, pos, hidden=False, params=None) -> 'Item':
        """ アイテムタイプに応じたインスタンスを生成するファクトリメソッド """
        item_class = ITEM_CLASS_MAP.get(type, Item)
        return item_class(id, type, pos, hidden, params)

class Key(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーにキー効果を適用する """
        pass

    def __repr__(self):
        return f"Key(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

class Weapon(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーに装備効果を適用する """
        pass

    def __repr__(self):
        return f"Weapon(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

class Potion(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーにポーション効果を適用する """
        pass

    def __repr__(self):
        return f"Potion(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

class Trap(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーに罠効果を適用する """
        pass

    def __repr__(self):
        return f"Trap(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

# アイテムタイプとクラスのマッピング
ITEM_CLASS_MAP = {
    "key": Key,
    "weapon": Weapon,
    "potion": Potion,
    "trap": Trap,
}

# ==================== ギミッククラス群 ====================

class Door:
    def __init__(self, id, pos, requires_key=None, opened=False):
        self.id = id
        self.pos = tuple(pos)
        self.requires_key = requires_key  # ドアに必要なキーID
        self.opened = opened
    
    def __repr__(self):
        return f"Door(id={self.id}, pos={self.pos}, requires_key={self.requires_key}, opened={self.opened})"

class Chest:
    def __init__(self, id, pos, requires_key=None, contents=[], opened=False):
        self.id = id
        self.pos = tuple(pos)
        self.requires_key = requires_key
        self.contents = contents  # item_id or 'gen:weapon:+3'
        self.opened = opened
    
    def __repr__(self):
        return f"Chest(id={self.id}, pos={self.pos}, requires_key={self.requires_key}, contents={self.contents}, opened={self.opened})"

class Teleport:
    def __init__(self, id, source, target, requires_key=None, bidirectional=True):
        self.id = id
        self.source = tuple(source)
        self.target = tuple(target)
        self.requires_key = requires_key
        self.bidirectional = bidirectional
    
    def __repr__(self):
        return f"Teleport(id={self.id}, source={self.source}, target={self.target}, requires_key={self.requires_key}, bidirectional={self.bidirectional})"


class Monster:
    def __init__(self, id, pos, ai_type, ai_params = {}, move_every=1, drop_list=[]):
        self.id = id  # 一意なID
        self.pos = tuple(pos)  # (row, col)

        self.ai_type = ai_type  # 'static'|'random'|'chase'|'patrol'
        self.ai_params = ai_params  # AIの行動についての追加パラメータ辞書

        self.move_every = move_every  # 何ターンごとに移動するか（0=動かない）
        self.turn_counter = 0  # ターンカウンター
        self.drop_list = drop_list  # 撃破時ドロップアイテムIDリスト
        
        # ステータスはフロア侵入時に自動で設定（要件）
        self.alive = True  # 生存フラグ
        self.hp = 0
        self.attack = 0
    
    def __repr__(self):
        return f"Monster(id={self.id}, pos={self.pos}, ai_type={self.ai_type}, ai_params={self.ai_params}, move_every={self.move_every}, drop_list={self.drop_list})"
    
    def init_status(self, player_hp, player_attack):
        """ プレイヤーステータスに基づき、モンスターのステータスを初期化する """  # TODO: ステータス設定 要調整
        self.hp = player_hp
        self.attack = player_attack

    def increment_turn(self):
        """ ターンカウンターを進める """
        if self.move_every > 0:
            self.turn_counter = (self.turn_counter + 1) % self.move_every
            if self.turn_counter == 0:
                return True
        return False

    def reset_turn_counter(self):
        """ ターンカウンターをリセットする """
        self.turn_counter = 0


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
    def __init__(self, start_pos: tuple[int, int]) -> None:
        self.hp = Player.MAX_HP
        self.attack = Player.BASE_ATK
        self.position = start_pos  # (row, col)
        # self.keys = set()
        self.inventory = {}  # id -> Item



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


def read_map_data(file_path: str) -> tuple[list[list[str]], str]:
    """
    map_txt を読み、[grid] と [info] を処理する。
    - [grid] は # と . のみ（検証は最小限）
    - [info] は json=xxx.json だけを見る
    返り値: (grid: List[List[str]], json_path: str)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    section = None
    grid = []
    json_path = ""
    info = {}

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue

        if line == "[grid]":
            section = 'grid'
            continue
        elif line == "[info]":
            section = 'info'
            continue

        if section == 'grid':
            grid.append(list(line))
            continue
        elif section == 'info':
            if line.startswith("json="):
                json_path = line.split("=", 1)[1].strip()
                continue

    return grid, json_path


# def print_grid(grid, info, player: Player = None):
#     for i in range(len(grid)):
#         row = []
#         for j in range(len(grid[i])):
#             if player is not None and (i, j) == player.position:
#                 row.append('@')
#             elif (i, j) == info.get('start'):
#                 row.append('S')
#             elif (i, j) == info.get('goal'):
#                 row.append('G')
#             elif grid[i][j] == '.':
#                 row.append(' ')
#             else:
#                 row.append(grid[i][j])

#         print("".join(row))


# プレイヤーからのコマンド入力を受け取る
def read_player_command() -> str:
    while True:
        command = input("(w/a/s/d 移動, u:ポーション, q:終了) > ").strip().lower()
        if command in ['w', 'a', 's', 'd', 'u', 'q']:
            return command
        print("不正ななコマンドです。{w, a, s, d, u, q} のいずれかを入力してください。")
        # print("Invalid command! Please enter w, a, s, d, u, or q.")


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
    map01 = MAP_DIR_PATH + "map01.txt"
    floor = Floor(map01)
    player = Player(start_pos=floor.start)

    floor.print_grid(player)
    print()

    while True:
        command = read_player_command()
        if command == 'q':
            print("ゲーム終了します。")
            break

        new_position = try_move_player(player, command, floor.grid)
        if new_position is not None:
            player.position = new_position
        else:
            print("その方向には移動できません！")

        if player.position == floor.info['goal']:
            print("ゴールに到達しました！")
            break
        
        print()
        floor.print_grid(player)
        print()


# Main ループ
def main():
    print_game_text(TEXT_DIR_PATH+"Firstgame_ui.txt")
    time.sleep(1)
    print_game_text(TEXT_DIR_PATH+"Basic_rule.txt")
    time.sleep(1)
    print_game_text(TEXT_DIR_PATH+"Opening.txt")
    time.sleep(1)
    # for i in range(5):
    #     palying_map = random_select_map()
    #     grid, info = read_map_data(MAP_DIR_PATH + palying_map[i])
    #     # print(info)
    #     # return
    #     player = Player(start=info['start'])

    #     print_grid(grid, info, player)

    #     while True:
    #         command = read_player_command()
    #         if command == 'q':
    #             print("Quitting the game.")
    #             break

    #         new_position = try_move_player(player, command, grid)
    #         if new_position is not None:
    #             player.position = new_position
    #         else:
    #             print("Cannot move in that direction!")
            
    #         if player.position == info['goal']:
    #             print("Reached the goal!")
    #             break

    #         print_grid(grid, info, player)


def tmp():
    map01 = MAP_DIR_PATH + "map01.txt"
    floor = Floor(map01)
    # floor = Floor(sample_map_data)
    # print_grid(floor.grid, )
    floor.print_info()
    floor.print_grid()

if __name__ == "__main__":
    # main()
    tmp_run_game()
    # tmp()