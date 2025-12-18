import random
import heapq
import math
from modules.floor import Floor
from modules.game_state import GameState
from modules.constants import DIRECTIONS

class RandomAI:
    def __init__(self, name="RandomAI"):
        self.name = name

    def decide_move(self, game_state: GameState):
        actions = game_state.get_legal_actions()
        return random.choice(actions)


class ModeBasedAI:
    ai_modes = ['WEAPON_SEARCH', 'POTION_SEARCH', 'USE_POTION', 'KEY_SEARCH', "HIDDEN_ITEM_SEARCH", 'MONSTER_HUNT', 'GOAL_SEARCH', 'EXPLORE']
    BASE_MOVE_COST = 1
    BASE_TRAP_COST = 1
    BASE_TERRAIN_DAMAGE_COST = 1

    INF = 10 ** 18

    def __init__(self, name="ModeBasedAI", game_state: GameState = None):
        self.name = name
        self.mode = "WEAPON_SEARCH"

        # self.not_enough_keys_counter = 0  # 鍵不足でゴールに到達できなかった回数
        # self.required_keys_for_goal = set()  # ゴールに到達するために必要な鍵．ゴールに到達時に更新される．フロアクリアでリセット．

        self.info_by_experience = {}  # 移動履歴に基づく情報辞書
        self.teleport_map = {}  # {source_pos: target_pos}
        self.known_teleport_cells = set()

        self.ice_regions = set()  # 氷セル集合


        print("[ModeBasedAI] Initialized")
        if game_state:
            info, _ = game_state.get_known_info()
            print(info)

            for gimmick in info['floor']['gimmicks']:
                if gimmick['type'] == 'ice':
                    self.ice_regions.update({tuple(pos) for pos in gimmick['positions']})


    def decide_move(self, game_state: GameState) -> str:
        # 情報取得
        info, legal_actions = game_state.get_known_info()
        player_pos = info['player']['position']
        floor_info = info['floor']

        # モード決定
        self.mode = self.decide_mode(game_state)
        print(f"[ModeBasedAI] Current mode: {self.mode}")

        if self.mode == "USE_POTION":
            return 'u'
        
        # モードに応じた目的地設定
        targets = set()
        
        if self.mode == "WEAPON_SEARCH":
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'weapon'}

        elif self.mode == "POTION_SEARCH":
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'potion'}

        elif self.mode == "KEY_SEARCH":
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'key'}

        elif self.mode == "HIDDEN_ITEM_SEARCH":
            targets = {tuple(pos) for pos in floor_info['hidden_items']}

        elif self.mode == "MONSTER_HUNT":
            # とりあえず全てのモンスターを候補にする（近い順に探索される）
            targets = {tuple(m['pos']) for m in floor_info['monsters']}

        elif self.mode == "GOAL_SEARCH":
            targets = {tuple(pos) for pos in floor_info['goal']}

        if not targets:
            raise Exception("ターゲットが見つからない")
        
        # ダイクストラ法で次の移動方向を決定
        best_move = self.dijkstra(player_pos, targets, info)

        # 経路が見つからない，または無効な手の場合はランダム（ポーション使用以外）
        if best_move == "" or best_move not in legal_actions:
            move_candidates = [a for a in legal_actions if a != 'u']
            return random.choice(move_candidates) if move_candidates else 'q'

        return best_move
    
    def decide_mode(self, game_state: GameState) -> str:
        info, _ = game_state.get_known_info()
        player_info = info['player']
        floor_info = info['floor']
        
        # HPが低ければポーション使用 最優先
        if player_info['hp'] <= 30 and player_info['potions']:
            return "USE_POTION"

        # 最初は武器探索モード
        if [item for item in floor_info['visible_items'] if item['type'] == "weapon"]:
            return "WEAPON_SEARCH"
        
        # ポーション探索
        if [item for item in floor_info['visible_items'] if item['type'] == "potion"] and len(player_info['potions']) < 3:
            return "POTION_SEARCH"

        # 見える鍵があれば鍵探索
        if [item for item in floor_info['visible_items'] if item['type'] == "key"]:
            return "KEY_SEARCH"
        
        if player_info['keys']:
            return "GOAL_SEARCH"

        # # 鍵を持っていたら，いったんゴールまで向かう
        # if player_info['keys'] and self.not_enough_keys_counter == 0:
        #     return "GOAL_SEARCH"
        
        # 隠しアイテム探索
        if floor_info['hidden_items']:
        # if floor_info['hidden_items'] and (self.required_keys_for_goal - set(player_info['keys'])):
            return "HIDDEN_ITEM_SEARCH"
        
        # ゴールに必要な鍵が足りない場合，モンスター討伐モード
        if floor_info['monsters']: 
            return "MONSTER_HUNT"
        
        raise Exception("いったんエラー")
        return "GOAL_SEARCH"

    # 戦闘ダメージ予測
    def _estimate_monster_damage(self, strength: str = 'normal', player_atk: int = 10) -> int:
        """ モンスターの強さから被ダメージを概算する """
        # 強さごとのステータス係数
        if strength == 'weak':
            monster_hp, m_atk = 30, 3  # ~0.3
        elif strength == 'normal':
            monster_hp, m_atk = 60, 6  # ~0.6
        elif strength == 'strong':
            monster_hp, m_atk = 100, 10 # ~1.0
        else:
            monster_hp, m_atk = 60, 6

        # 戦闘シミュレーション（プレイヤー先攻）
        # プレイヤーが倒すのにかかるターン数
        turns_to_kill = math.ceil(monster_hp / player_atk)
        # モンスターから受ける攻撃回数
        turns_taken = max(0, turns_to_kill - 1)
        
        return turns_taken * m_atk


    # ステップコスト計算
    def calculate_step_cost(self, pos: tuple[int, int], info: dict) -> int:
        """
        指定した座標 pos に踏み込む際にかかるコストを計算する。
        基本移動コスト + 罠 + 地形ダメージ + モンスター戦闘ダメージ
        """
        
        total_cost = self.BASE_MOVE_COST
        
        player_info = info['player']
        floor_info = info['floor']
        
        # 1. 罠コスト
        for item in floor_info['visible_items']:
            if tuple(item['pos']) == pos and item['type'] == 'trap':
                total_cost += self.BASE_TRAP_COST
        
        # 2. 地形ダメージコスト
        for gimmick in floor_info['gimmicks']:
            if gimmick['type'] == 'terrain_damage':
                if pos in gimmick['positions']:
                    total_cost += self.BASE_TERRAIN_DAMAGE_COST  # 地形ダメージを加算 TODO: デフォルトで1にしているが，経験によって推定コストを変更したい．
        
        # 3. モンスター戦闘コスト
        for monster in floor_info['monsters']:
            if tuple(monster['pos']) == pos:
                damage = self._estimate_monster_damage(
                    monster['strength'], 
                    player_info['attack']
                )
                
                # 「倒さないと通れない」かつ「負ける（HP以上のダメージ）」場合，通行不可
                if damage >= player_info['hp']:
                    return self.INF
                
                total_cost += damage
                
        return total_cost

    # 経路探索
    def dijkstra(self, start_pos: tuple[int, int], targets: set[tuple[int, int]], info: dict) -> str:
        """
        ダイクストラ法を用いてターゲットまでの最短（最小コスト）経路を探索する。
        最初の一歩の方向('w', 'a', 's', 'd')を返す
        """
        grid = info['floor']['grid']
        rows = len(grid)
        cols = len(grid[0])
        
        
        # 優先度付きキュー: (累積コスト, 現在座標, 最初の一歩の方向)
        pq = [(0, start_pos, "")]
        
        # 訪問済みコスト管理: 座標 -> 最小コスト
        min_costs = {start_pos: 0}
        
        directions = {
            'w': (-1, 0), 
            'a': (0, -1), 
            's': (1, 0), 
            'd': (0, 1)
            }

        while pq:
            current_cost, current_pos, first_move = heapq.heappop(pq)
            
            # 記録されているコストより大きい場合はスキップ
            if current_cost > min_costs.get(current_pos, self.INF):
                continue
            
            # ターゲット到達判定
            if current_pos in targets:
                return first_move
            
            # 隣接ノード探索
            for move_dir in directions:
                next_pos, step_cost, traversed_positions = self.simulate_move(current_pos, move_dir, info)
                
                # 通行不可（勝ち目のないモンスターなど）の場合はスキップ
                if step_cost == self.INF:
                    continue
                
                new_cost = current_cost + step_cost
                next_first_move = first_move if first_move else move_dir

                # 氷床上を滑っている途中でもアイテムを取得できるため途中経路も確認
                if any(pos in targets for pos in traversed_positions):
                    return next_first_move
                
                # コスト更新判定
                if new_cost < min_costs.get(next_pos, self.INF):
                    min_costs[next_pos] = new_cost
                    heapq.heappush(pq, (new_cost, next_pos, next_first_move))

        return ""  # 経路が見つからない場合
    
    def simulate_move(self, start_pos: tuple[int, int], move_dir_char: str, info: dict) -> tuple[tuple[int, int], int, list[tuple[int, int]]]:
        """
        ある位置からある方向へ移動した際の結果をシミュレーションする。 iceによる滑りと，teleportによる移動を考慮．
        return: 到達座標, 移動コスト, 通過した座標リスト
        """
        dr, dc = DIRECTIONS[move_dir_char]
        grid = info['floor']['grid']
        rows, cols = len(grid), len(grid[0])

        next_r, next_c = start_pos[0] + dr, start_pos[1] + dc
        
        # 壁判定
        if not (0 <= next_r < rows and 0 <= next_c < cols) or grid[next_r][next_c] != '.':
            return start_pos, self.INF, []

        # 閉じたドア判定
        closed_doors = {tuple(d['pos']) for d in info['floor']['doors'] if not d['opened']}
        if (next_r, next_c) in closed_doors:
            return start_pos, self.INF, []

        current_pos = (next_r, next_c)
        total_cost = self.calculate_step_cost(current_pos, info)  # 1歩目のコスト


        path_positions = [current_pos] # 通過した座標（Iceスライド用）

        # Ice ギミック 
        ice_regions = set()
        for gimmick in info['floor']['gimmicks']:
            if gimmick['type'] == 'ice':
                ice_regions.update({tuple(pos) for pos in gimmick['positions']})
            elif gimmick['type'] == 'terrain_damage':
                continue  # 地形ダメージはすでにコスト計算に反映済み
        
        if current_pos in ice_regions:
            while True:
                slide_r = current_pos[0] + dr
                slide_c = current_pos[1] + dc

                # 滑り先の壁・範囲外チェック
                if not (0 <= slide_r < rows and 0 <= slide_c < cols):
                    break # 壁で停止
                if grid[slide_r][slide_c] != '.':
                    break # 壁で停止
                if (slide_r, slide_c) in closed_doors:
                    break # ドアで停止

                # 次のマスが有効なので移動
                current_pos = (slide_r, slide_c)

                # 滑り中のコスト加算
                step_cost = self.calculate_step_cost(current_pos, info)
                total_cost += step_cost
                path_positions.append(current_pos)

                if current_pos not in ice_regions:
                    break  # 氷以外のセルに到達したら停止
        
        # Teleport ギミック
        if current_pos in self.teleport_map:
            target_pos = self.teleport_map[current_pos]
            current_pos = target_pos
            total_cost += self.calculate_step_cost(current_pos, info)
        
        return current_pos, total_cost, path_positions




