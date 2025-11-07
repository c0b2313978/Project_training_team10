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
    
    def use_potion(self, item_id: str) -> bool:
        """ ポーションを使用する """
        item = self.inventory.get(item_id)
        if item is None or item.type != 'potion':
            print("そのポーションは持っていません。")
            return False
        
        # ポーション効果適用
        item.apply_effect(self)
        print(f"ポーション {item_id} を使用しました。")
        
        # インベントリから削除
        del self.inventory[item_id]
        return True
    
    def item_organizing(self) -> None:
        """ インベントリ内のアイテムを整理する（種類ごとにまとめるなど）, inventoryの内容が変更された場合に呼び出す """
        organized_inventory = []
        type_counter = Counter()
        for item in self.inventory.values():
            type_counter[item.type] += 1
            organized_inventory.append((item.type, type_counter[item.type], item))