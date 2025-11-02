# ==================== モンスタークラス ====================

import random
from modules.constants import DIRECTIONS

class Monster:
    def __init__(self, id, pos, ai_type, ai_params = {}, move_every=1, drop_list=[]):
        self.id = id  # 一意なID
        self.pos = tuple(pos)  # (row, col)
        self.next_pos = self.pos  # 次のターンの位置

        self.ai_type = ai_type  # 'static'|'random'|'chase'|'patrol'
        self.ai_params = ai_params  # AIの行動についての追加パラメータ辞書

        self.move_every = move_every  # 何ターンごとに移動するか（0=動かない）
        self.turn_counter = 0  # ターンカウンター
        self.drop_list = drop_list  # 撃破時ドロップアイテムIDリスト
        
        # ステータスはフロア侵入時に自動で設定（要件）
        self.alive = True  # 生存フラグ
        self.hp = 0
        self.attack = 0
        self.init_status()  # ステータス初期化

        # デバッグ用表示
        self.debug_path = []  # デバッグ用：移動経路記録リスト
    
    def __repr__(self):
        return f"Monster(id={self.id}, pos={self.pos}, ai_type={self.ai_type}, ai_params={self.ai_params}, move_every={self.move_every}, drop_list={self.drop_list})"
    
    def init_status(self, player_hp: int = 50, player_attack: int = 10):
        """ プレイヤーステータスに基づき、モンスターのステータスを初期化する """  # TODO: ステータス設定 要調整
        self.hp = player_hp
        self.attack = player_attack

        # ai_params
        if self.ai_type == 'patrol':
            self.patrol_points = [tuple(p) for p in self.ai_params.get('points', [])]
            self.patrol_point = 0  # 現在のパトロールポイントインデックス

    def increment_turn(self):
        """ ターンカウンターを進める """
        if self.move_every > 0:
            self.turn_counter = (self.turn_counter + 1) % self.move_every
            if self.turn_counter == 0:
                return True
        return False

    def reset_turn_counter(self):
        """ ターンカウンターをリセットする """
        self.turn_counter = 0
    
    # ===== モンスター行動 =====
    def monster_next_move(self, player_pos: tuple[int, int], grid: list[list[str]]) -> tuple[int, int]:
        """ モンスターのAIによる移動先決定ロジック """
        # static: 動かない
        if self.ai_type == 'static':
            return self.pos
        
        # random: ランダム移動
        elif self.ai_type == 'random':
            moveable_positions = []
            for direction in DIRECTIONS.values():
                new_row = self.pos[0] + direction[0]
                new_col = self.pos[1] + direction[1]
                if not (0 <= new_row < len(grid) and 0 <= new_col < len(grid[0])):
                    continue  # マップ外

                if grid[new_row][new_col] == '.':  # 通路なら移動可能
                    moveable_positions.append((new_row, new_col))
            
            if moveable_positions:  # 移動可能な場所がある場合
                p = self.ai_params.get('p', 0.5)  # 移動確率
                if random.random() < p:
                    return random.choice(moveable_positions)  # ランダムに移動先選択
        
        # chase: プレイヤーに向かって移動
        elif self.ai_type == 'chase':
            # 幅優先探索で最短経路を見つける
            path = self.bfs(self.pos, player_pos, grid)
            if path and len(path) > 1:
                return path[1]
        
        # patrol: パトロール移動
        elif self.ai_type == 'patrol':
            
            if not self.patrol_points:
                return self.pos  # パトロールポイント未設定なら移動しない

            # 最も近いパトロールポイントを目指す
            target_point = self.patrol_points[self.patrol_point]
            if self.pos == target_point:  # 現在のパトロールポイントに到達したら次へ
                self.patrol_point = (self.patrol_point + 1) % len(self.patrol_points)
                target_point = self.patrol_points[self.patrol_point]
            path = self.bfs(self.pos, target_point, grid)
            if path and len(path) > 1:
                return path[1]
            
        return self.pos  # デフォルト：移動しない
    
    def bfs(self, start: tuple[int, int], goal: tuple[int, int], grid: list[list[str]]) -> list[tuple[int, int]]:
        """ 幅優先探索で最短経路を見つける """
        from collections import deque

        n, m = len(grid), len(grid[0])
        visited = set()
        prev = {start: None}  # 経路復元用辞書
        queue = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()
            if current == goal:
                break

            for dr, dc in DIRECTIONS.values():
                new_row = current[0] + dr
                new_col = current[1] + dc
                new_pos = (new_row, new_col)

                if not (0 <= new_row < n and 0 <= new_col < m):
                    continue  # マップ外
                if grid[new_row][new_col] != '.':
                    continue  # 通路でない
                if new_pos in visited:
                    continue  # 訪問済み

                visited.add(new_pos)
                prev[new_pos] = current
                queue.append(new_pos)

        # 経路復元
        path = []
        step = goal
        while step is not None:
            path.append(step)
            step = prev.get(step)
        path.reverse()
        self.debug_path = path  # デバッグ用：移動経路記録リストに保存

        if path[0] == start:
            return path  # 最短経路
        else:
            return []  # 経路なし


# テストコード
if __name__ == "__main__":
    import json
    from modules.floor import Floor
    from modules.constants import sample_map_data
    floor = Floor(sample_map_data)

