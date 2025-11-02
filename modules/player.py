# ==================== プレイヤークラス ====================

from modules.items import Item

class Player:
    MAX_HP = 100
    BASE_ATK = 10
    def __init__(self, start_pos: tuple[int, int]) -> None:
        self.hp = Player.MAX_HP
        self.attack = Player.BASE_ATK
        self.position = start_pos  # (row, col)
        # self.keys = set()
        self.inventory = {}  # id -> Item
        self.visited_cells = set()  # 訪問済みセル集合
    
    # ====== ステータス表示 ======
    def print_status(self) -> None:
        """ プレイヤーステータスを表示する """
        print(f"HP: {self.hp}/{Player.MAX_HP}, Attack: {self.attack}")
        self.print_inventory()
    
    # ====== インベントリ 管理 ======
    def print_inventory(self) -> None:
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