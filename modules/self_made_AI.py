import random
from modules.floor import Floor
from modules.game_state import GameState
from modules.player import Player
from modules.items import Item, Weapon, Potion, Key, Trap




class RandomAI:
    def __init__(self, name="RandomAI"):
        self.name = name

    def decide_move(self, game_state: GameState):
        actions = game_state.get_legal_actions()
        return random.choice(actions)


class ModeBasedAI:
    ai_modes = ['WEAPON_SEARCH', 'POTION_SEARCH', 'USE_POTION', 'KEY_SEARCH', "HIDDEN_ITEM_SEARCH", 'MONSTER_HUNT', 'GOAL_SEARCH', 'EXPLORE']
    def __init__(self, name="ModeBasedAI"):
        self.name = name
        self.mode = "WEAPON_SEARCH"

        self.not_enough_keys_counter = 0  # 鍵不足でゴールに到達できなかった回数
        self.required_keys_for_goal = set()  # ゴールに到達するために必要な鍵．ゴールに到達時に更新される．フロアクリアでリセット．

    def decide_move(self, game_state: GameState) -> str:
        self.mode = self.decide_mode(game_state)
        print(f"[ModeBasedAI] Current mode: {self.mode}")

        if self.mode == "USE_POTION":
            return 'u'
        
        if self.mode == "WEAPON_SEARCH":
            pass

        if self.mode == "POTION_SEARCH":
            pass

        if self.mode == "KEY_SEARCH":
            pass

        if self.mode == "HIDDEN_ITEM_SEARCH":
            pass

        if self.mode == "MONSTER_HUNT":
            pass

        if self.mode == "GOAL_SEARCH":
            pass

        return ""
    
    def decide_mode(self, game_state: GameState) -> str:
        info, _ = game_state.get_known_info()
        player_info = info['player']
        floor_info = info['floor']
        
        # HPが低ければポーション使用 最優先
        if player_info['hp'] <= 30 and game_state.player.potions:
            return "USE_POTION"

        # 最初は武器探索モード
        if [item for item in floor_info['visible_items'].values() if item.type == "weapon"]:
            return "WEAPON_SEARCH"
        
        # ポーション探索
        if [item for item in floor_info['visible_items'].values() if item.type == "potion"] and len(player_info['potions']) < 3:
            return "POTION_SEARCH"

        # 見える鍵があれば鍵探索
        if [key for key in floor_info['visible_items'].values() if key.type == "key"]:
            return "KEY_SEARCH"

        # 鍵を持っていたら，いったんゴールまで向かう
        if player_info['keys'] and self.not_enough_keys_counter == 0:
            return "GOAL_SEARCH"
        
        # 隠しアイテム探索
        if [item for item in floor_info['hidden_items'].values()] and self.required_keys_for_goal - player_info['keys']:
            return "HIDDEN_ITEM_SEARCH"
        
        # ゴールに必要な鍵が足りない場合，モンスター討伐モード
        if [monster for monster in floor_info['visible_monsters'].values()] and self.required_keys_for_goal - player_info['keys']: 
            return "MONSTER_HUNT"
        
        return "GOAL_SEARCH"

    # 経路コスト計算
    def calculate_path_cost(self) -> int:
        # 目的地までの経路上に存在する罠やダメージ床による HP 減少量をコストに加算
        # モンスター: 
            # 「倒さない通れない」かつ「勝てる」場合，先頭によるHP減少量をコストに加算
            # 「倒さないと通れない」かつ「負ける」場合，通行不可
        return 0


    # ダイクストラ
    def dijkstra(self, start_pos: tuple[int, int], targets: set[tuple[int, int]], floor: Floor) -> str:
        from collections import deque

        directions = {'w': (-1, 0), 'a': (0, -1), 's': (1, 0), 'd': (0, 1)}
        queue = deque([(start_pos, [])])  # (current_pos, path)
        visited = set()
        
        while queue:
            current_pos, path = queue.popleft()
            if current_pos in visited:
                continue
            visited.add(current_pos)

            if current_pos in targets:
                return path[0] if path else ''

            for direction, (dr, dc) in directions.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                if floor.is_moveable(next_pos) and next_pos not in visited:
                    queue.append((next_pos, path + [direction]))
        
        return ''  # 到達不可能な場合