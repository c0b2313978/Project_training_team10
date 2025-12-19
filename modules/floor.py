# ==================== フロアクラス ====================
import json
from modules.items import Item
from modules.objects import Door, Chest, Teleport, Gimmicks
from modules.player import Player
from modules.monsters import Monster
from modules.read_map_data import read_map_data

# マップを表示する際のシンボル定義 半角
ENTITY_SYMBOLS = {
    "player": "@",
    "goal": "G",
    "path": " ",
    "wall": "■",
    "weapon": "W",
    "potion": "P",
    "key": "K",
    "trap": "!",
    "monster": "M",
    "opened_door": "/",
    "closed_door": "D",
    "closed_chest": "C",
    "opened_chest": " ",
    "teleport": "T",
    "hidden_item": "?",
}

# マップを表示する際のシンボル定義 全角
ENTITY_SYMBOLS_FULL_WIDTH = {
    "player": "🧍",
    "goal": "🚩",
    "path": "　",
    "wall": "🔳",
    "weapon": "🗡️ ", 
    "potion": "🧪",
    "key": "🔑",
    "trap": "💥",
    "monster": "👾",
    "monster_weak": "🐁",  # ここ
    "monster_normal": "👾",
    "monster_strong": "🐉",
    "opened_door": "　",
    "closed_door": "🚪",
    "closed_chest": "🧰",
    "opened_chest": "　",
    "teleport": "🔯",
    "hidden_item": "❓",
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

        # # ===== ギミック =====
        self.gimmick: Gimmicks | None = None
        self._gimmicks_init()

        # ===== ルール =====
        self.rule = ""
        self._rules_init()

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

    # ===== ギミック情報初期化 =====
    def _gimmicks_init(self):
        gimmicks_data = self.info.get('gimmicks')
        if isinstance(gimmicks_data, dict) and gimmicks_data:
            self.gimmicks = Gimmicks(grid=self.grid, moveable_cells=self.movable_cells, params=gimmicks_data)
        else:
            self.gimmicks = None


    def _rules_init(self):
        self.rule = self.info.get('rule', "")

    def print_info(self):
        """ フロア情報を表示する（デバッグ用） """
        print(f"Floor Name: {self.name}")
        print(f"Map Size: {self.map_size}")
        print(f"Start Position: {self.start}")

        print("Goal Info:")
        print(self.goal)

        print("Items:")
        print(self.items)
        
        print("Monsters:")
        print(self.monsters)

        print("Doors:")
        print(self.doors)

        print("Chests:")
        print(self.chests)

        print("Teleports:")
        print(self.teleports)

    # ===== マップ上のシンボル収集 =====
    def _collect_entity_symbols(self, full_width = True) -> dict[tuple[int, int], str]:
        """ マップ上のアイテム・モンスター・ギミックのシンボルを収集し、位置とシンボルの辞書を返す """
        symbol_map = ENTITY_SYMBOLS_FULL_WIDTH if full_width else ENTITY_SYMBOLS

        symbols: dict[tuple[int, int], str]= {}  # 位置: シンボルのタイプ
        # items
        for item in self.items.values():
            if item.picked:  # 回収済みアイテム
                continue
            if item.hidden and self.reveal_hidden:  # 未発見の隠しアイテム
                symbols[item.pos] = "hidden_item"
            else:
                symbols[tuple(item.pos)] = item.type

        # monsters
        for monster in self.monsters.values():
            if monster.alive:
                monster_strength_key = f"monster_{monster.strength}"
                symbols[monster.pos] = monster_strength_key if (monster_strength_key in symbol_map) else "monster"

        # doors
        for door in self.doors.values():
            symbols[door.pos] = "opened_door" if door.opened else "closed_door"

        # chests
        for chest in self.chests.values():
            symbols[chest.pos] = "opened_chest" if chest.opened else "closed_chest"

        # teleports
        for tp in self.teleports.values():
            symbols[tp.source] = "teleport"
            if tp.bidirectional:
                symbols[tp.target] = "teleport"
        return symbols

    # ===== マップ表示 =====
    def print_grid(self, player: Player = None, output_file_object = None, full_width: bool = True, coordinate_display: bool = True) -> str:
        """
        マップ全体を表示する
        引数:
            player: プレイヤーオブジェクトを指定すると、プレイヤー位置を表示する
            full_width: True なら全角シンボル、False なら半角シンボルで表示する
            output_file_object: ファイルオブジェクトを指定すると、そこに出力する（デフォルトは標準出力）
            coordinate_display: True なら行列番号を表示する (0-indexed)
        返り値: 
            出力したマップ文字列
        """
        entity_symbols = self._collect_entity_symbols()
        symbol_map = ENTITY_SYMBOLS_FULL_WIDTH if full_width else ENTITY_SYMBOLS
        output = ""  # 出力用文字列
        
        if coordinate_display:  # 列番号表示
            output += "　" if full_width else " "  # 左上隅スペース
            for col in range(self.map_size[1]):
                output += f"{col:2}" if full_width else f"{col:>2}"  # 列番号追加
            output += "\n"

        for i in range(self.map_size[0]):
            row = []
            if coordinate_display:
                row.append(f"{i:<2}" if full_width else f"{i:>2}")  # 行番号追加
            
            for j in range(self.map_size[1]):
                pos = (i, j)
                if player is not None and pos == player.position:  # プレイヤー位置
                    symbol = symbol_map["player"]
                elif pos in self.goal['pos']:  # ゴール位置
                    symbol = symbol_map["goal"]
                elif pos in entity_symbols:  # アイテム・モンスター・ギミック
                    symbol = symbol_map[entity_symbols[pos]]
                elif self.grid[i][j] == '.':  # 通路
                    symbol = symbol_map["path"]
                else:
                    symbol = symbol_map["wall"]  # 壁
                
                row.append(symbol)

            output += "".join(row) + "\n"

        print(output, file=output_file_object)
        return output


    # ==================== イベント処理 ====================
    def _handle_cell_items(self, player: Player, cell_pos: tuple[int, int]) -> None:
        for item in self.items.values():
            if item.picked or item.pos != cell_pos:
                continue  # 位置が違うか、既に回収済み

            if item.hidden and not self.reveal_hidden:
                continue  # 隠しアイテムは発見されない

            if item.type in ('trap', 'weapon'):  # 罠・武器の即時効果適用
                item.apply_effect(player)
                item.picked = True
            else:
                player.add_item(item)
                item.picked = True
                print(f"アイテム {item.id} ({item.type}) を取得しました。")

    # ===== 踏んだ瞬間の処理 を一括で行う =====
    def enter_cell(self, player: Player) -> None:
        """ プレイヤーがセルに入った際のイベント処理 """
        traversed_positions = [player.position]
        if self.gimmicks and self.gimmicks.is_ice_cell(player.position):
            self.gimmicks.ice_gimmick_effect(player, on_visit=traversed_positions.append)  # 氷床ギミック処理

        for pos in traversed_positions:  # 通過した全セルに対して処理
            self._handle_cell_items(player, pos)
            if self.gimmicks:  # ダメージ床
                damage = self.gimmicks.apply_terrain_damage(player, pos)
                if damage:
                    print(f"足元のダメージ床で {damage} ダメージを受けた！ (残りHP: {player.hp})")
        
        # テレポート
        for teleport in self.teleports.values():
            new_pos = teleport.get_destination(player.position)
            if new_pos is not None:
                player.position = new_pos
                break


    # ===== モンスターとの戦闘処理 =====
    def battle_monster(self, player: Player, monster: Monster) -> None:
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
                for drop_item in monster.drop_list:
                    item = Item.create_item(**drop_item)  # Itemオブジェクト生成
                    if item.type == 'trap' or item.type == 'weapon':  # 即時効果適用アイテム
                        item.apply_effect(player)
                    else:
                        player.add_item(item)  # 鍵, ポーションはインベントリに追加
                break

            # モンスターの攻撃
            player.hp -= monster.attack
            print(f"モンスター {monster.id} の攻撃！ あなたは {monster.attack} のダメージを受けました！ (残りHP: {max(player.hp, 0)})")
            if player.hp <= 0:
                print("あなたは倒されてしまいました...")
                break


    # ===== ゴール判定 =====
    def check_goal(self, player: Player) -> tuple[bool, str]:
        """ ゴール条件を満たしているか判定する
        返り値:
            (is_goal: bool, goal_message: str)
        """
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


# Floor 実験用コード
# python -m modules.floor
if __name__ == "__main__":
    map_file = "map_data/map06.txt"
    # map_file = "map_data/sample01.txt"
    floor = Floor(map_file, floor_id="1")
    floor.print_info()
    floor.print_grid(full_width=True)
