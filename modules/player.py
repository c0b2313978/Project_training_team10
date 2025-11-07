# ==================== プレイヤークラス ====================
from collections import Counter
from modules.items import Item

class Player:
    MAX_HP = 100
    BASE_ATK = 10
    def __init__(self, start_pos: tuple[int, int]) -> None:
        self.hp = Player.MAX_HP
        self.attack = Player.BASE_ATK
        self.position = start_pos  # (row, col)

        self.inventory: dict[str, Item] = {}  # id -> Item
        self.keys: set[str] = set()  # 所持しているキーID集合
        self.potions: dict[str, Item] = {}  # 所持ポーション
        
        # self.visited_cells = set()  # 訪問済みセル集合
    
    # ====== ステータス表示 ======
    def print_status(self) -> None:
        """ プレイヤーステータスを表示する """
        print(f"HP: {self.hp}/{Player.MAX_HP}, Attack: {self.attack}")
        self.print_inventory()
    
    # ====== インベントリ 管理 ======
    def print_inventory(self, debug: bool = False) -> None:
        """ インベントリを表示する """
        print("Inventory:")
        if not self.inventory:
            print("\t(空)")
            return
        for id, item in self.inventory.items():
            print(f"\t{item}: {id}")
    
    def add_item(self, item: Item) -> None:  # TODO: アイテムの種類によって保存場所変えるかも
        """ アイテムをインベントリに追加する """
        self.inventory[item.id] = item

        if item.type == 'potion':  # ポーション獲得時にストック数を増やす
            self.potions[item.id] = item
    
    def use_potion(self) -> bool:
        """ ポーションを使用する """
        if not self.potions:
            print("使用可能なポーションがありません！")
            return False
        
        # インベントリからポーションを探す
        potion = self.potions.popitem()[1]  # 1つ取得

        # ポーション効果適用
        potion.apply_effect(self)
        print(f"ポーション {potion.id} を使用しました。")

        # インベントリから削除
        del self.inventory[potion.id]
        return True
    
    def item_organizing(self) -> None:
        """ インベントリ内のアイテムを整理する（種類ごとにまとめるなど）, inventoryの内容が変更された場合に呼び出す """
        organized_inventory = []
        type_counter = Counter()
        for item in self.inventory.values():
            type_counter[item.type] += 1
            organized_inventory.append((item.type, type_counter[item.type], item))