"""
modules.self_made_AI の Docstring
"""

import random
import heapq
import math
from modules.constants import DIRECTIONS

class RandomAI:
    def __init__(self, name="RandomAI"):
        self.name = name

    def decide_move(self, info: dict, legal_actions: list[str]) -> str:
        return random.choice(legal_actions)


class ModeBasedAI:
    ai_modes = ['WEAPON_SEARCH', 'POTION_SEARCH', 'USE_POTION', 'KEY_SEARCH', "HIDDEN_ITEM_SEARCH", 'MONSTER_HUNT', 'GOAL_SEARCH', 'EXPLORE', 'TELEPORT_EXPLORE']
    BASE_MOVE_COST = 1
    BASE_TRAP_COST = 1
    BASE_TERRAIN_DAMAGE_COST = 1
    MAX_HP = 100

    INF = 10 ** 18  # 通行不可コスト

    def __init__(self, name="ModeBasedAI", output_file_object = None):
        self.name = name
        self.output_file_object = output_file_object

        self.mode = "WEAPON_SEARCH"  # 現在のAIモード
        self.previous_floor_id = -1  # 1ターン前のフロアID
        self.current_floor_id = -1  # 現在のフロアID

        self.previous_position = (-1, -1) # 1ターン前の位置
        self.current_position = (-1, -1)  # 現在位置
        self.previous_direction = ""    # 1ターン前の移動方向
        self.current_direction = ""     # 現在の移動方向

        # テレポート情報: {source_pos: {"target": target_pos, "confirmed": bool}}
        self.teleport_map: dict[tuple[int, int], dict] = {}
        self.ice_regions = set()  # 氷セル集合


    # ===== メイン処理 =====
    def decide_move(self, info: dict, legal_actions: list[str], output_debug=False) -> str:
        """
        次の移動方向を決定する
        info, legal_actions は GameState.get_known_info() から取得したもの
        return: w|a|s|d|u
        """
        # === 情報更新 ===
        floor_info = info['floor']
        player_info = info['player']

        # フロア移動検出
        self.current_floor_id = floor_info['id']
        if self.previous_floor_id != self.current_floor_id:
            self._init_info_on_floor_change(floor_info=floor_info)
            
            if output_debug: 
                print(f"[{self.name}] Floor changed to {self.current_floor_id}", file=self.output_file_object)
                print(f"Floor info: {floor_info}", file=self.output_file_object)

        # プレイヤー位置更新
        player_pos = tuple(player_info['position'])
        self.previous_position = self.current_position
        self.current_position = player_pos

        # テレポートギミックの情報を経験から更新
        self._update_teleport_map_from_last_turn(floor_info=floor_info, player_info=player_info)
        
        # モード決定
        self.mode = self.decide_mode(floor_info=floor_info, player_info=player_info)

        # ポーション使用モードなら即使用
        if self.mode == "USE_POTION":
            return 'u'
        
        # === モードに応じた目的地設定 ===
        targets = set()
        
        if self.mode == "WEAPON_SEARCH":
            # 武器の位置をターゲットに
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'weapon'}

        elif self.mode == "POTION_SEARCH":
            # ポーションの位置をターゲットに
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'potion'}

        elif self.mode == "KEY_SEARCH":
            # 鍵の位置をターゲットに
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'key'}

        elif self.mode == "HIDDEN_ITEM_SEARCH":
            # 隠しアイテムの位置をターゲットに
            targets = {tuple(pos) for pos in floor_info['hidden_items']}

        elif self.mode == "MONSTER_HUNT":
            # 全てのモンスターの位置をターゲットに
            targets = {tuple(m['pos']) for m in floor_info['monsters']}

        elif self.mode == "GOAL_SEARCH":
            # ゴール位置をターゲットに
            targets = {tuple(pos) for pos in floor_info['goal']}

        if not targets:
            # ターゲットが見つからない場合は例外
            raise Exception("ターゲットが見つからない")
        
        # ダイクストラ法で次の移動方向を決定
        best_move, best_path = self.dijkstra(
            start_pos = player_pos, 
            targets = targets, 
            floor_info = floor_info, 
            player_info = player_info
        )
        
        # 経路が見つからず，未調査テレポートがあれば探索モードに切り替え
        if best_move == "" and self.mode != "TELEPORT_EXPLORE":
            teleport_targets = {pos for pos, info in self.teleport_map.items() if not info['confirmed']}
            if teleport_targets:
                self.mode = "TELEPORT_EXPLORE"
                best_move, best_path = self.dijkstra(
                    start_pos = player_pos,
                    targets = teleport_targets,
                    floor_info = floor_info,
                    player_info = player_info
                )
        
        if output_debug:
            print(f"[{self.name}] Current mode: {self.mode}", file=self.output_file_object)
            print(f"[{self.name}] Player pos: {player_pos}", file=self.output_file_object)
            print(f"[{self.name}] Targets: {targets}", file=self.output_file_object)
            print(f"[{self.name}] Best path: {best_path}", file=self.output_file_object)

        # 経路上のモンスターが現HPだと倒せない場合は，先にポーション使用を優先
        if player_info['potions'] and player_info['hp'] < self.MAX_HP and best_path:
            for monster in floor_info['monsters']:
                if tuple(monster['pos']) in best_path:
                    damage = self._estimate_monster_damage(monster['strength'], player_info['attack'])
                    if damage >= player_info['hp']:
                        return 'u'

        # 経路が見つからない，または無効な手の場合はランダム（ポーション使用以外）
        final_move = best_move
        if final_move == "" or final_move not in legal_actions:
            move_candidates = [a for a in legal_actions if a != 'u']
            final_move = random.choice(move_candidates) if move_candidates else 'q'

        # AI状態更新
        self.previous_direction = self.current_direction
        self.current_direction = final_move
        return final_move
    

    def decide_mode(self, floor_info: dict, player_info: dict) -> str:
        """ ゲーム状況に応じてAIモードを決定する """

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
        
        # 隠しアイテム探索
        if floor_info['hidden_items']:
            return "HIDDEN_ITEM_SEARCH"
        
        # ゴールに必要な鍵が足りない場合，モンスター討伐モード
        if floor_info['monsters']: 
            return "MONSTER_HUNT"
        
        return "GOAL_SEARCH"
    
    
    def _init_info_on_floor_change(self, floor_info: dict):
        """ フロア移動時の情報初期化 """
        # フロアID更新
        self.previous_floor_id = self.current_floor_id

        # 位置・方向情報初期化
        self.previous_position = (-1, -1)
        self.current_position = (-1, -1)
        self.previous_direction = ""
        self.current_direction = ""

        # ギミック情報初期化
        self.teleport_map = {}
        self._teleport(floor_info)
        self.ice_regions = set()
        for gimmick in floor_info['gimmicks']:
            if gimmick['type'] == 'ice':
                self.ice_regions.update({tuple(pos) for pos in gimmick['positions']})
            elif gimmick['type'] == 'terrain_damage':
                pass  # 地形ダメージは現状未使用

    def _update_teleport_map_from_last_turn(self, floor_info: dict, player_info: dict) -> None:
        """
        直前ターンの行動から teleport を推定して teleport_map を更新する．
        - 前ターン開始位置: self.previous_position
        - 前ターン行動: self.current_direction
        - 実際の現在位置: self.current_position
        """
        if self.previous_position == (-1, -1):
            return

        last_action = self.current_direction
        if last_action not in DIRECTIONS:
            return

        # テレポートを考慮しないで移動した場合の到達点を計算
        end_before_teleport, step_cost, _ = self.simulate_move(
            start_pos = self.previous_position, 
            move_dir = last_action, 
            floor_info = floor_info, 
            player_info = player_info, 
            consider_teleport = False
        )
        if step_cost == self.INF:
            return

        # テレポートが発生した場合はマップに記録
        if end_before_teleport in self.teleport_map and end_before_teleport != self.current_position:
            self.teleport_confirm(end_before_teleport, self.current_position)

    # ===== teleportギミック関連 =====
    def _teleport(self, floor_info: dict):
        """
        teleportギミックの情報を初期化・更新する
        - テレポートマスが2マスのみである場合，双方向だと仮定して情報を登録する
        - それ以外の場合，位置のみ登録し，経験に基づいて情報を更新していく
        """
        # floor_info から teleport ギミックの位置を取得
        teleport_positions = floor_info['teleports'] # {(r, c), ...}
        if len(teleport_positions) == 2:
            pos1, pos2 = teleport_positions
            self.teleport_map[pos1] = {"target": pos2, "confirmed": False}
            self.teleport_map[pos2] = {"target": pos1, "confirmed": False}
        else:
            for pos in teleport_positions:
                if pos not in self.teleport_map:
                    self.teleport_map[pos] = {"target": (-1, -1), "confirmed": False}
    
    def teleport_confirm(self, source_pos: tuple[int, int], target_pos: tuple[int, int]):
        """ テレポートギミックの情報を記録する（確定） """
        self.teleport_map[source_pos] = {"target": target_pos, "confirmed": True}
    

    def teleport_suspect(self, source_pos: tuple[int, int], target_pos: tuple[int, int]):
        """ テレポートギミックの仮情報を記録する（未確定） """
        if source_pos in self.teleport_map and not self.teleport_map[source_pos]['confirmed']:
            self.teleport_map[source_pos] = {"target": target_pos, "confirmed": False}
    
    
    # 戦闘ダメージ予測
    def _estimate_monster_damage(self, strength: str = 'normal', player_atk: int = 10) -> int:
        """ プレイヤーの攻撃力とモンスターの強さから，プレイヤーの被ダメージを概算する """
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
    def calculate_step_cost(self, position: tuple[int, int], floor_info: dict, player_info: dict) -> int:
        """
        指定した座標 pos に踏み込む際にかかるコストを計算する．
        基本移動コスト + 罠 + 地形ダメージ + モンスター戦闘ダメージ
        """
        total_cost = self.BASE_MOVE_COST
        
        # 1. 罠コスト
        for item in floor_info['visible_items']:
            if tuple(item['pos']) == position and item['type'] == 'trap':
                total_cost += self.BASE_TRAP_COST
        
        # 2. 地形ダメージコスト
        for gimmick in floor_info['gimmicks']:
            if gimmick['type'] == 'terrain_damage':
                if position in gimmick['positions']:
                    total_cost += self.BASE_TERRAIN_DAMAGE_COST  # 地形ダメージを加算 TODO: デフォルトで1にしているが，経験によって推定コストを変更したい．
        
        # 3. モンスター戦闘コスト
        for monster in floor_info['monsters']:
            if tuple(monster['pos']) == position:
                damage = self._estimate_monster_damage(monster['strength'], player_info['attack'])
                
                # 「倒さないと通れない」かつ「負ける（HP以上のダメージ）」場合，通行不可
                if damage >= player_info['hp']:
                    if player_info['potions'] and damage < self.MAX_HP:
                        pass  # ポーションで回復可能なら通行可
                    else:
                        return self.INF  # 通行不可
                
                total_cost += damage
                
        return total_cost

    # 経路探索
    def dijkstra(self, start_pos: tuple[int, int], targets: set[tuple[int, int]], floor_info: dict, player_info: dict) -> tuple[str, list[tuple[int, int]]]:
        """
        ダイクストラ法を用いてターゲットまでの最短（最小コスト）経路を探索する．
        最初の一歩の方向('w', 'a', 's', 'd')を返す
        return: (first_move, path_positions)
        """
        grid = floor_info['grid']
        
        # 優先度付きキュー: (累積コスト, 現在座標, 最初の一歩の方向, 経路)
        pq = [(0, start_pos, "", [start_pos])]
        
        # 訪問済みコスト管理: 座標 -> 最小コスト
        min_costs = {start_pos: 0}

        while pq:
            current_cost, current_pos, first_move, path = heapq.heappop(pq)
            
            # 記録されているコストより大きい場合はスキップ
            if current_cost > min_costs.get(current_pos, self.INF):
                continue
            
            # ターゲット到達判定
            if current_pos in targets:
                return first_move, path
            
            # 隣接ノード探索
            for move_dir in DIRECTIONS:
                # 移動シミュレーション
                next_pos, step_cost, traversed_positions = self.simulate_move(start_pos=current_pos, move_dir=move_dir, floor_info=floor_info, player_info=player_info)
                
                # 通行不可（勝ち目のないモンスターなど）の場合はスキップ
                if step_cost == self.INF:
                    continue
                
                new_cost = current_cost + step_cost
                next_first_move = first_move if first_move else move_dir
                new_path = path + traversed_positions
                if not new_path or next_pos != new_path[-1]:
                    new_path = new_path + [next_pos]

                # 氷床上を滑っている途中でもアイテムを取得できるため途中経路も確認  TODO: 効率化の余地あり
                for i, pos in enumerate(traversed_positions):
                    if pos in targets:
                        return next_first_move, path + traversed_positions[:i + 1]
                
                # コスト更新判定
                if new_cost < min_costs.get(next_pos, self.INF):
                    min_costs[next_pos] = new_cost
                    heapq.heappush(pq, (new_cost, next_pos, next_first_move, new_path))

        return "", []  # 経路が見つからない場合
    
    def simulate_move(self, start_pos: tuple[int, int], move_dir: str, floor_info: dict, player_info: dict, consider_teleport: bool = True) -> tuple[tuple[int, int], int, list[tuple[int, int]]]:
        """
        ある位置からある方向へ移動した際の結果をシミュレーションする． iceによる滑りと，teleportによる移動を考慮．
        return: 到達座標, 移動コスト, 通過した座標リスト
        """
        dr, dc = DIRECTIONS[move_dir]
        grid = floor_info['grid']
        rows, cols = len(grid), len(grid[0])

        next_r, next_c = start_pos[0] + dr, start_pos[1] + dc
        
        # 壁判定
        if not (0 <= next_r < rows and 0 <= next_c < cols) or grid[next_r][next_c] != '.':
            return start_pos, self.INF, []

        # 閉じたドア判定
        closed_doors = {tuple(d['pos']) for d in floor_info['doors'] if not d['opened']}
        if (next_r, next_c) in closed_doors:
            return start_pos, self.INF, []

        current_pos = (next_r, next_c)
        total_cost = self.calculate_step_cost(position=current_pos, floor_info=floor_info, player_info=player_info)  # 1歩目のコスト

        path_positions = [current_pos] # 通過した座標（Iceスライド用）

        # Ice ギミック 
        if current_pos in self.ice_regions:
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

                next_pos = (slide_r, slide_c)
                if next_pos not in self.ice_regions:
                    break  # 氷の外には滑り出さない

                # 次のマスが有効なので移動
                current_pos = next_pos

                # 滑り中のコスト加算
                step_cost = self.calculate_step_cost(position=current_pos, floor_info=floor_info, player_info=player_info)
                total_cost += step_cost
                path_positions.append(current_pos)
        
        # Teleport ギミック
        if consider_teleport and current_pos in self.teleport_map and self.teleport_map[current_pos]['target'] != (-1, -1):
            current_pos = self.teleport_map[current_pos]['target']  # テレポート先に移動

        return current_pos, total_cost, path_positions
