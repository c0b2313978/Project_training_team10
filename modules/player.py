# ==================== プレイヤークラス ====================
from collections import Counter
from modules.items import Item

class Player:
    MAX_HP = 100
    BASE_ATK = 10
    def __init__(self, start_pos: tuple[int, int]) -> None:
        self.position = start_pos  # (row, col)

        self.hp = Player.MAX_HP
        self.equipped_weapon_attack = 0  # 装備武器の攻撃力
        self.equipped_weapon_id: str | None = None
        self.recalculate_attack()

        self.inventory: dict[str, Item] = {}  # id -> Item
        self.keys: set[str] = set()  # 所持しているキーID集合
        self.potions: set[str] = set()  # 所持ポーションID集合
        
        self.last_move_direction: str | None = None  # 最後に移動した方向 ('w', 'a', 's', 'd')
        # self.visited_cells = set()  # 訪問済みセル集合
        
    # ====== ステータス表示 ======
    def print_status(self, output_file_object=None) -> None:
        """ プレイヤーステータスを表示する """
        print(f"HP: {self.hp}/{Player.MAX_HP}, Attack: {self.attack}", file=output_file_object)
        self.print_inventory(output_file_object=output_file_object)
    
    # ====== インベントリ 管理 ======
    def print_inventory(self, debug: bool = False, output_file_object=None) -> None:
        """ インベントリを表示する """
        print("Inventory:", file=output_file_object)
        if debug:
            for id, item in self.inventory.items():
                print(f"\t{item}: {id}", file=output_file_object)
        else:
            if self.potions:
                print(f"\tPotions: {'🧪' * len(self.potions)}", file=output_file_object)
            
            if self.keys:  # キーid一覧を表示 だったやつをアイコンの個数で表現するようにした
                print(f"\tKeys: {'🔑' * len(self.keys)}", file=output_file_object)
        
        if self.equipped_weapon_id:
            print(f"\tWeapon: {self.equipped_weapon_id} (+{self.equipped_weapon_attack})", file=output_file_object)
        else:
            print("\tWeapon: None", file=output_file_object)

    def add_item(self, item: Item) -> None:
        """ アイテムをインベントリに追加する """
        self.inventory[item.id] = item

        if item.type == 'potion':  # ポーション獲得時にポーション集合に追加
            self.potions.add(item.id)

        elif item.type == 'key':  # キー獲得時にキー集合に追加
            self.keys.add(item.id)

    def floor_clear_keys_reset(self) -> None:
        """ フロアクリア時に鍵だけリセットする """
        self.keys.clear()
        key_ids = [key_id for key_id in self.inventory if self.inventory[key_id].type == 'key']
        for key_id in key_ids:
            del self.inventory[key_id]
    
    def use_potion(self, output_file_object=None) -> bool:
        """ ポーションを使用する """
        if not self.potions:
            print("使用可能なポーションがありません！", file=output_file_object)
            return False
        
        # インベントリからポーションを探す
        potion_id = self.potions.pop()  # 1つ取得

        # ポーション効果適用
        self.inventory[potion_id].apply_effect(self, output_file_object=output_file_object)
        print(f"ポーション {potion_id} を使用しました。", file=output_file_object)

        # インベントリから削除
        del self.inventory[potion_id]
        return True
    
    def recalculate_attack(self) -> None:
        """ 基礎攻撃力と装備ボーナスで攻撃力を更新 """
        self.attack = Player.BASE_ATK + self.equipped_weapon_attack

    def equip_weapon(self, weapon: Item, attack_bonus: int, output_file_object=None) -> None:
        """ 武器は1本のみ装備し、強い方へ自動で持ち替える """
        if attack_bonus <= self.equipped_weapon_attack:
            print(f"{weapon.id} を拾ったが、すでに装備中の武器の方が強い。", file=output_file_object)
            return

        self.equipped_weapon_id = weapon.id
        self.equipped_weapon_attack = attack_bonus
        self.recalculate_attack()
        print(f"{weapon.id} に持ち替えた。攻撃力は {self.attack} になった。", file=output_file_object)
    
    def item_organizing(self) -> None:
        """ インベントリ内のアイテムを整理する（種類ごとにまとめるなど）, inventoryの内容が変更された場合に呼び出す """
        organized_inventory = []
        type_counter = Counter()
        for item in self.inventory.values():
            type_counter[item.type] += 1
            organized_inventory.append((item.type, type_counter[item.type], item))
