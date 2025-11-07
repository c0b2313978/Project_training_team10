
# ==================== ギミッククラス群 ====================
from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING: 
    from modules.player import Player
from modules.items import Item, Key, Weapon, Potion, ITEM_CLASS_MAP
from modules.constants import DIRECTIONS

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
        self.contents: list[dict] = contents  # id, type, params の辞書リスト
        self.opened = opened
    
    def __repr__(self):
        return f"Chest(id={self.id}, pos={self.pos}, requires_key={self.requires_key}, contents={self.contents}, opened={self.opened})"
    
    def return_contents(self) -> list[Item]:
        """ contents を実体化して返す """
        items = []
        for content in self.contents:
            item = Item.create_item(**content)
            if item:
                items.append(item)
        return items


class Teleport:
    def __init__(self, id, source, target, requires_key=None, bidirectional=True):
        self.id = id
        self.source = tuple(source)
        self.target = tuple(target)
        self.requires_key = requires_key
        self.bidirectional = bidirectional
    
    def __repr__(self):
        return f"Teleport(id={self.id}, source={self.source}, target={self.target}, requires_key={self.requires_key}, bidirectional={self.bidirectional})"
    
    # ===== from_pos から見た destination を返す =====
    def get_destination(self, from_pos: tuple[int, int]) -> tuple[int, int] | None:
        if from_pos == self.source:
            return self.target
        elif self.bidirectional and from_pos == self.target:  # 双方向テレポートの場合
            return self.source
        else:
            return None

# ==================== ギミック全体クラス ====================
class Gimmicks:
    def __init__(self, grid: list[list[str]], moveable_cells: set[tuple[int, int]] | None = None, params: dict | None = None):
        self.grid = grid  # floorのグリッド情報参照用
        if moveable_cells is None:
            moveable_cells = {(i, j) for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] == '.'}
        self.moveable_cells = set(moveable_cells)  # 移動可能セル集合
        self.params = params or {}

        self.is_ice = 'ice' in self.params  # ギミックに氷が含まれているか
        self.ice_regions: set[tuple[int, int]] = self._normalize_region_list(self.params.get('ice'))

        self.is_terrain_damage = 'terrain_damage' in self.params  # ギミックに地形ダメージが含まれているか
        terrain_config = self.params.get('terrain_damage', {})
        if self.is_terrain_damage:
            regions = terrain_config.get('regions', self.moveable_cells)
            self.terrain_damage_regions = {tuple(pos) for pos in regions}
            self.terrain_damage = terrain_config.get('damage', 1)  # ダメージ量（デフォルト1）
        else:
            self.terrain_damage_regions = set()
            self.terrain_damage = 0

    def _normalize_region_list(self, raw_regions) -> set[tuple[int, int]]:
        if raw_regions is None:
            return set()
        if isinstance(raw_regions, dict):
            candidates = raw_regions.get('regions', self.moveable_cells)
        else:
            candidates = raw_regions
        return {tuple(pos) for pos in candidates}

    def is_gimmick_cell(self, pos: tuple[int, int]) -> bool:
        """ 指定された位置が指定されたギミックのセルかどうかを判定する """
        if self.is_ice and pos in self.ice_regions:
            return True
        if self.is_terrain_damage and pos in self.terrain_damage_regions:
            return True
        return False

    def is_ice_cell(self, pos: tuple[int, int]) -> bool:
        return self.is_ice and pos in self.ice_regions

    # ===== ギミックの種類ごとの動作メソッド群 =====
    def ice_gimmick_effect(self, player: Player, on_visit: Callable[[tuple[int, int]], None] | None = None) -> None:
        """ プレイヤーが氷上にいる場合にスライド効果を適用する """
        current_position = player.position  # プレイヤーの現在位置
        if current_position not in self.ice_regions:
            return  # 氷上にいない場合は何もしない
        direction = player.last_move_direction
        if direction is None:
            return  # 最後の移動方向が不明な場合は何もしない
        
        dx, dy = DIRECTIONS[direction]
        while True:
            next_position = (current_position[0] + dx, current_position[1] + dy)
            # 次の位置が移動可能セルであり、氷上である場合は移動を続ける
            if next_position in self.ice_regions and next_position in self.moveable_cells:
                current_position = next_position
                if on_visit:
                    on_visit(current_position)
            else:
                break
        
        player.position = current_position  # 最終的な位置に更新
    
    
    def terrain_damage_value(self, pos: tuple[int, int]) -> int:
        """ 指定された位置での地形ダメージ量を返す """
        if not self.is_terrain_damage or pos not in self.terrain_damage_regions:
            return 0
        return self.terrain_damage

    def apply_terrain_damage(self, player: Player, pos: tuple[int, int]) -> int:
        """ 指定された位置で地形ダメージを Player に適用し、実際に与えたダメージ量を返す """
        damage = self.terrain_damage_value(pos)
        if damage <= 0:
            return 0
        player.hp = max(player.hp - damage, 0)
        return damage



