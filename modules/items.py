from typing import TYPE_CHECKING
import random
if TYPE_CHECKING: 
    from modules.player import Player

# ==================== アイテムクラス群 ====================
class Item:
    def __init__(self, id, type, pos = (-1, -1), hidden=False, params=None):
        self.id = id                # 一意なID
        self.type = type            # 'weapon'|'potion'|'key'|'trap'
        self.pos = tuple(pos)              # (row, col)
        self.hidden = hidden        # 描画する際に隠れているかどうか
        self.params = params or {}  # 追加パラメータ辞書
        self.picked = False         # 回収済みかどうか
    
    def __repr__(self):
        return f"Item(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーにアイテム効果を適用する（サブクラスでオーバーライド） """
        pass

    @classmethod
    def create_item(cls, id, type, pos = (-1, -1), hidden=False, params=None) -> 'Item':
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
    DEFAULT_ATTACK = 10
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーに装備効果を適用する """
        attack_bonus = self.params.get('atk', random.randint(1, self.DEFAULT_ATTACK))
        player.equip_weapon(self, attack_bonus)

    def __repr__(self):
        return f"Weapon(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"


class Potion(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーにポーション効果を適用する """
        player.hp = player.MAX_HP  # HP全回復（仮）

    def __repr__(self):
        return f"Potion(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"


class Trap(Item):
    DEFAULT_DAMAGE = 10
    def apply_effect(self, player: 'Player') -> None:
        """ プレイヤーに罠効果を適用する """
        damage = self.params.get('damage', self.DEFAULT_DAMAGE)  # ダメージ量
        player.hp -= damage
        print(f"罠にかかりました！ {damage} のダメージを受けました。")

    def __repr__(self):
        return f"Trap(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden}, params={self.params})"

class Dummy(Item):
    def apply_effect(self, player: 'Player') -> None:
        """ 何も効果を発揮しないアイテム """
        pass

    def __repr__(self):
        return f"Dummy(id={self.id}, type={self.type}, pos={self.pos}, hidden={self.hidden})"

# アイテムタイプとクラスのマッピング
ITEM_CLASS_MAP = {
    "key": Key,
    "weapon": Weapon,
    "potion": Potion,
    "trap": Trap,
    "Dummy": Dummy,
}
