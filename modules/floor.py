# ==================== フロアクラス ====================
import json
from pprint import pprint
from modules.items import Item
from modules.objects import Door, Chest, Teleport, Gimmicks
from modules.monsters import Monster
from modules.read_map_data import read_map_data

# マップを表示する際のシンボル定義
ENTITY_SYMBOLS = {
    "item": {"weapon": "W", "potion": "P", "key": "K", "trap": "!"},
    "monster": "M",
    "door": lambda door: "/" if door.opened else "D",
    "chest": lambda chest: "C" if not chest.opened else "c",
    "teleport": lambda tp: "T",
    "hidden_item": "?",
}

class Floor:
    """
    map_txt から読み込んだ1フロア分の全データ（grid以外はJSONから供給）
    grid: 2次元リスト（#と.のみ）
    json_path: JSONデータのパス
    以下はJSONで与える:
        name, reveal_hidden, start, goal, goal.type/keys
        items, monsters, doors, chests, teleports, gimmicks
    
    フロア内のイベント処理はここで行う。
    """
    def __init__(self, map_file_path: str, specific_json_path: str = "", floor_id: str = "-1") -> None:
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

    # ===== JSONデータ読み込み =====
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

    # ===== マップ表示 =====
    def print_grid(self, player: 'Player' = None):
        """マップ全体を表示する"""
        entity_symbols = self._collect_entity_symbols()

        for i in range(self.map_size[0]):
            row = []
            for j in range(self.map_size[1]):
                pos = (i, j)
                if player is not None and pos == player.position:  # プレイヤー位置
                    row.append('@')
                # elif pos == self.start:  # スタート位置
                #     row.append('S')  # TODO: もしかしたらいらないかも？
                elif pos in self.goal['pos']:  # ゴール位置
                    row.append('G')
                elif pos in entity_symbols:  # アイテム・モンスター・ギミック
                    row.append(entity_symbols[pos])
                elif self.grid[i][j] == '.':  # 通路
                    row.append(' ')
                else:
                    row.append(self.grid[i][j])  # 壁

            print("".join(row))
    
    # ==================== イベント処理 ====================
    # ===== 踏んだ瞬間の処理 を一括で行う =====
    def enter_cell(self, player: 'Player') -> None:
        """ プレイヤーがセルに入った際のイベント処理 """
        # アイテム取得・罠発動
        for item in self.items.values():
            if (item.pos != player.position) or item.picked:
                continue  # 位置が違うか、既に回収済み

            if item.hidden and not self.reveal_hidden:
                continue  # 隠しアイテムは発見されない

            # 罠・武器の即時効果適用
            if item.type == 'trap' or item.type == 'weapon':
                item.apply_effect(player)
                item.picked = True  # 罠・武器は回収済みにする
            else:
                # アイテム取得処理
                player.add_item(item)
                item.picked = True
                print(f"アイテム {item.id} ({item.type}) を取得しました。")

    # # ===== モンスターとの遭遇判定 =====
    # def check_monster_encounter(self, player: 'Player') -> Monster | None:
    #     """ プレイヤーがモンスターと遭遇したか判定し、遭遇した場合はそのモンスターを返す """
    #     for monster in self.monsters.values():
    #         if monster.alive and monster.pos == player.position:
    #             return monster
    #     return None
    
    # ===== モンスターとの戦闘処理 =====
    def battle_monster(self, player: 'Player', monster: Monster) -> None:
        """ プレイヤーとモンスターの戦闘処理 """
        # print(f"モンスター {monster.id} と遭遇しました！ 戦闘開始！")

        while player.hp > 0 and monster.hp > 0:
            # プレイヤーの攻撃
            monster.hp -= player.attack
            print(f"あなたの攻撃！ モンスター {monster.id} に {player.attack} のダメージ！ (残りHP: {max(monster.hp, 0)})")
            if monster.hp <= 0:
                monster.alive = False
                print(f"モンスター {monster.id} を倒しました！")
                # ドロップアイテム処理
                for drop_id in monster.drop_list:
                    drop_item = self.items.get(drop_id)
                    if drop_item and not drop_item.picked:
                        player.add_item(drop_item)
                        drop_item.picked = True
                        print(f"モンスターがアイテム {drop_item.id} ({drop_item.type}) をドロップしました。取得しました！")
                break

            # モンスターの攻撃
            player.hp -= monster.attack
            print(f"モンスター {monster.id} の攻撃！ あなたは {monster.attack} のダメージを受けました！ (残りHP: {max(player.hp, 0)})")
            if player.hp <= 0:
                print("あなたは倒されてしまいました...")
                break

    # def generate_drop_items(self, monster: 'Monster') -> list[Item]:
    #     """ モンスター撃破時のドロップアイテムリストを生成する """
    #     drop_items = []
    #     for drop_id in monster.drop_list:
    #         drop_item = self.items.get(drop_id)
    #         if drop_item and not drop_item.picked:
    #             drop_items.append(drop_item)
    #     return drop_items

    # ===== ゴール判定 =====
    def check_goal(self, player: 'Player') -> tuple[bool, str]:
        goal_message = "ゴール条件を満たしました！"

        # reach | keys_only | reach_and_keys
        if self.goal['type'] == 'reach':
            if player.position not in self.goal['pos']:
                return False, ""
            else:
                return True, goal_message

        elif self.goal['type'] == 'keys_only':
            for key_id in self.goal['keys']:
                if key_id not in player.inventory:
                    return False, "必要な鍵が足りません。"
            return True, goal_message

        elif self.goal['type'] == 'reach_and_keys':
            if player.position not in self.goal['pos']:
                return False, ""
            for key_id in self.goal['keys']:
                if key_id not in player.inventory:
                    return False, "必要な鍵が足りません。"
            return True, goal_message

        else:
            return False, "ゴール条件を満たしていません。"

