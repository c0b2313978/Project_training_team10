
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

# ==================== ギミック全体クラス ====================
class Gimmicks:
    def __init__(self):
        self.ice_regions = []      # list of sets/rects → 下でセル集合化
        self.ice_cells = set()     # 実体（セル集合）
        self.slide_triggers_each_cell = True
        self.hp_drain_per_step = 0
        self.monster_can_enter_ice = True
        self.trap_cells = set()    # 地形的罠セル（ダメ10など簡易）