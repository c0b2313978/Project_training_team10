"""
ModeBasedAI クラス (line: 142 ~) 概説

状況に応じた「モード」を決定し，ダイクストラ法を用いてターゲットへの最短（最小コスト）経路を算出するAI．
氷床の滑りやテレポートの学習など，フロアギミックの挙動をシミュレーションに組み込んでいる．

decide_move (line: 175 ~ 296)
    ゲーム情報を受け取り，次の行動コマンドを決定する．
    Args:
        - info: ゲーム状態（プレイヤー，フロア，アイテム等）の辞書．
        - legal_actions: 実行可能な行動のリスト．
    処理の流れ:
        1. フロア情報の更新 (line: 183 ~ 194)
            - 現在のフロアIDを取得する．
            - フロアIDが直前と異なる場合，_init_info_on_floor_change を呼び出し情報をリセットする．
        2. プレイヤー位置の更新 (line: 196 ~ 199)
            - 直前の位置と現在の位置を更新する．
        3. テレポート情報の更新 (line: 202)
            - _update_teleport_map_from_last_turn を呼び出し，前ターンの移動結果からテレポートの接続先を推定・更新する．
        4. モード決定 (line: 206 ~ 210)
            - decide_mode を呼び出し，現在の状況に最適なモードを決定する．
            - モードが 'USE_POTION' の場合，即座に 'u' を返す．
        5. ターゲット設定 (line: 212 ~ 241)
            - モードに応じて，フロア情報から目的地（ターゲット）の座標集合を作成する．
            - WEAPON_SEARCH: 見えている武器の座標．
            - POTION_SEARCH: 見えているポーションの座標．
            - KEY_SEARCH: 見えている鍵の座標．
            - HIDDEN_ITEM_SEARCH: 隠しアイテムの座標．
            - MONSTER_HUNT: 全モンスターの座標．
            - GOAL_SEARCH: ゴールの座標．
        6. 経路探索 (line: 246 ~ 251)
            - dijkstra メソッドを呼び出し，現在地からターゲットへの最適ルートと最初の一手を算出する．
        7. テレポート探索への切り替え (line: 256 ~ 265)
            - 経路が見つからず，かつ未確定のテレポートマスが存在する場合，モードを 'TELEPORT_EXPLORE' に変更する．
            - 未確定テレポートマスをターゲットとして再度 dijkstra を実行する．
        8. 安全確認とコマンド決定 (line: 275 ~ 290)
            - 算出された経路上に「現在のHPで倒せないモンスター」が存在し，かつポーション所持かつHP回復で耐えられる場合，行動を 'u' (ポーション使用) に変更する．
            - 経路がない，または無効な手の場合，合法手から 'u' 以外をランダム選択する．
        9. 状態更新と返り値 (line: 292 ~ 295)
            - 直前と現在の移動方向変数を更新し，決定したコマンドを返す．

decide_mode (line: 298 ~ 329)
    優先順位に基づいてAIの行動モードを決定する．
    処理の流れ:
        以下の順序で条件を判定し，最初に合致したモードを返す．
        1. HPが30以下 かつ ポーション所持 -> 'USE_POTION'
        2. フロアに武器が存在する -> 'WEAPON_SEARCH'
        3. フロアにポーションが存在 かつ 所持数3未満 -> 'POTION_SEARCH'
        4. フロアに鍵が存在する -> 'KEY_SEARCH'
        5. プレイヤーが鍵を所持している -> 'GOAL_SEARCH'
        6. 隠しアイテムが存在する -> 'HIDDEN_ITEM_SEARCH'
        7. モンスターが存在する（鍵ドロップ狙い） -> 'MONSTER_HUNT'
        8. 上記以外 -> 'GOAL_SEARCH'

_init_info_on_floor_change (line: 332 ~ 353)
    フロア移動時に内部情報をリセットする．
    処理内容:
        - 位置，方向の変数を初期化する．
        - テレポートマップを空にし，_teleport メソッドで初期情報を登録する．
        - フロア情報の gimmicks から氷床の位置情報を取得し，ice_regions セットを更新する．

_update_teleport_map_from_last_turn (line: 356 ~ 384)
    直前の行動結果からテレポートのリンク情報を確定させる．
    処理内容:
        - 直前の位置から simulate_move を実行（テレポート考慮なし）し，予測される移動先座標を算出する．
        - 予測座標がテレポートマスであり，かつ実際の現在地と異なる場合，テレポートが発生したと判断する．
        - teleport_confirm を呼び出し，予測座標から現在地へのリンクを確定情報として記録する．

_teleport (line: 386 ~ 401)
    フロア開始時にテレポート情報を初期化する．
    処理内容:
        - テレポートマスがちょうど2つの場合，相互リンク（双方向）と仮定して確定情報を登録する．
        - それ以外の場合，リンク先不明の未確定情報として位置のみ登録する．

teleport_confirm / teleport_suspect (line: 403 ~ 411)
    テレポートマップへの情報の登録．
    処理内容:
        - confirm: リンク先と 'confirmed': True を設定する．
        - suspect: リンク先と 'confirmed': False を設定する（現状コードでは未使用）．

_estimate_monster_damage (line: 415 ~ 433)
    モンスターとの戦闘による被ダメージを予測する．
    処理内容:
        - モンスターの強さ（weak/normal/strong）に応じたHPと攻撃力を設定する．
        - プレイヤーがモンスターを倒すまでのターン数を計算する．
        - (ターン数 - 1) × モンスター攻撃力 を被ダメージとして返す．

calculate_step_cost (line: 436 ~ 469)
    特定のマスへ進入する際のコストを計算する．
    処理内容:
        - 基本移動コスト（1）を設定する．
        - 罠がある場合，コストを加算する（+10）．
        - ダメージ床がある場合，コストを加算する（+1）．
        - モンスターがいる場合:
            - 戦闘ダメージを予測し，コストに加算する．
            - ダメージが現在HP以上の場合（ポーション回復不能時），コストを無限大（INF）とし通行不可とする．

dijkstra (line: 472 ~ 526)
    ダイクストラ法による経路探索を行う．
    Args:
        - start_pos: 開始座標．
        - targets: 目的地の座標集合．
    Returns:
        - 最短経路の最初の一手（方向文字）と，経路座標のリスト．
    処理の流れ:
        - 優先度付きキューと最小コスト管理辞書を初期化する．
        - キューが空になるまで以下を繰り返す:
            1. 最低コストのノードを取り出す．
            2. 現在地が targets に含まれていれば，その時点の「最初の一手」と「経路」を返す．
            3. 上下左右の各方向について simulate_move を実行する．
            4. 移動コストが無限大ならスキップする．
            5. 移動経路（滑り移動含む）の途中にターゲットが含まれるか確認し，あれば即座に返す．
            6. 新しいコストが最小コストを更新する場合，キューに追加する．
        - 経路が見つからない場合，空文字と空リストを返す．

simulate_move (line: 528 ~ 592)
    1手移動した後の座標，コスト，通過経路をシミュレーションする．
    処理の流れ:
        1. 壁，閉じたドア，マップ外判定を行い，移動不可ならコスト無限大を返す．
        2. calculate_step_cost で1歩目のコストを計算する．
        3. 氷床（ice）ギミック処理:
            - 現在地が氷床である限り，進行方向へ滑り移動を繰り返す．
            - 壁，ドア，氷床外に出るまでループし，通過マスのコストを加算し続ける．
        4. テレポートギミック処理:
            - 到達地点が確定済みテレポートマスなら，リンク先へ座標を更新する．
        5. 最終的な到達座標，累積コスト，通過した座標リストを返す．
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
    # AIが取りうる行動モード一覧
    ai_modes = ['WEAPON_SEARCH', 'POTION_SEARCH', 'USE_POTION', 'KEY_SEARCH', "HIDDEN_ITEM_SEARCH", 'MONSTER_HUNT', 'GOAL_SEARCH', 'EXPLORE', 'TELEPORT_EXPLORE']
    BASE_MOVE_COST = 1  # 1歩あたりの基本コスト
    BASE_TRAP_COST = 10  # 罠を踏むコスト
    BASE_TERRAIN_DAMAGE_COST = 1  # ダメージ床のコスト
    MAX_HP = 100
    INF = 10 ** 18  # 通行不可を表す無限大コスト（勝てないモンスターなど）

    def __init__(self, name="ModeBasedAI", output_file_object = None):
        self.name = name
        self.output_file_object = output_file_object

        # 行動決定に関する状態変数
        self.mode = "WEAPON_SEARCH"  # 現在のAIモード

        # フロア遷移検出用のID保持
        self.previous_floor_id = -1  # 1ターン前のフロアID
        self.current_floor_id = -1  # 現在のフロアID

        # 位置・移動方向の履歴（テレポート学習用）
        self.previous_position = (-1, -1) # 1ターン前の位置
        self.current_position = (-1, -1)  # 現在位置
        self.previous_direction = ""    # 1ターン前の移動方向
        self.current_direction = ""     # 現在の移動方向

        # マップ知識
        # テレポート情報: {source_pos: {"target": target_pos, "confirmed": bool}}
        self.teleport_map: dict[tuple[int, int], dict] = {}
        self.ice_regions = set()  # 氷セルの座標集合


    # ===== メイン処理 =====
    def decide_move(self, info: dict, legal_actions: list[str], output_debug=False) -> str:
        """AIのメインループ．現在のゲーム状態から次の行動を決定する．
        Args:
            info (dict): GameState.get_known_info() から取得したゲーム情報
            legal_actions (list): 現在実行可能なコマンドのリスト
        Returns: 
            str: 決定した行動コマンド ('w', 'a', 's', 'd', 'u')
        """
        # === 情報の更新とフロア移動検出 ===
        floor_info = info['floor']
        player_info = info['player']

        self.current_floor_id = floor_info['id']
        # フロアが変わった場合，マップ知識（テレポートや履歴）をリセットする
        if self.previous_floor_id != self.current_floor_id:
            self._init_info_on_floor_change(floor_info=floor_info)
            
            if output_debug: 
                print(f"[{self.name}] Floor changed to {self.current_floor_id}", file=self.output_file_object)
                print(f"Floor info: {floor_info}", file=self.output_file_object)

        # プレイヤー位置更新
        player_pos = player_info['position']
        self.previous_position = self.current_position
        self.current_position = player_pos

        # 前ターンの行動と現在の位置を照らし合わせ，テレポートが発生したかを確認・記録する
        self._update_teleport_map_from_last_turn(floor_info=floor_info, player_info=player_info)
        
        # === モード決定 ===
        # HP，所持アイテム，フロアアイテムの状況から優先順位に基づいてモードを決定
        self.mode = self.decide_mode(floor_info=floor_info, player_info=player_info)

        # ポーション使用モードなら即使用
        if self.mode == "USE_POTION":
            return 'u'
        
        # === モードに応じた目的地設定 ===
        targets = set()
        
        if self.mode == "WEAPON_SEARCH":
            # フロア内の見える武器を全てターゲットにする
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'weapon'}

        elif self.mode == "POTION_SEARCH":
            # フロア内の見えるポーションを全てターゲットにする
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'potion'}

        elif self.mode == "KEY_SEARCH":
            # フロア内の見える鍵を全てターゲットにする
            targets = {tuple(item['pos']) for item in floor_info['visible_items'] if item['type'] == 'key'}

        elif self.mode == "HIDDEN_ITEM_SEARCH":
            # マップ上で '?' と表示されている隠しアイテムの場所をターゲットにする
            targets = {tuple(pos) for pos in floor_info['hidden_items']}

        elif self.mode == "MONSTER_HUNT":
            # モンスター討伐（主に鍵ドロップ狙い）のため，全モンスターの位置をターゲットにする
            targets = {tuple(m['pos']) for m in floor_info['monsters']}

        elif self.mode == "GOAL_SEARCH":
            # ゴール座標をターゲットにする
            targets = {tuple(pos) for pos in floor_info['goal']}

        if not targets:
            # 論理的にあり得ないはずだが，ターゲットが空の場合は例外
            raise Exception("ターゲットが見つからない")
        
        # === 経路探索 (ダイクストラ法) ===
        # 現在地からターゲット集合への最短経路（最小コスト経路）を探索
        # best_move: 最初の一手 ('w', 'a', 's', 'd'), best_path: 経路の座標リスト
        best_move, best_path = self.dijkstra(
            start_pos = player_pos, 
            targets = targets, 
            floor_info = floor_info, 
            player_info = player_info
        )
        
        # === リカバリー策: 未知のテレポート探索 ===
        # ターゲットへの有効な経路が見つからず，かつ未確定のテレポートマスがある場合
        # モードを強制的に「テレポート探索」に切り替え，テレポートの飛び先を解明しに行く
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

        # === 安全確認 ===
        # 算出した経路上にモンスターが存在する場合，今のHPで勝てるか判定する
        if player_info['potions'] and player_info['hp'] < self.MAX_HP and best_path:
            for monster in floor_info['monsters']:
                if tuple(monster['pos']) in best_path:
                    # 被ダメージ予測
                    damage = self._estimate_monster_damage(monster['strength'], player_info['attack'])
                    # 戦闘で死ぬ可能性があるなら，移動よりも回復(u)を優先する
                    if damage >= player_info['hp']:
                        return 'u'

        # === 最終決定 ===
        # 経路が見つからない，または算出された手が合法手でない場合（壁に向かうなど）
        final_move = best_move
        if final_move == "" or final_move not in legal_actions:
            # ポーション使用('u')以外のランダム移動を試みる
            move_candidates = [a for a in legal_actions if a != 'u']
            final_move = random.choice(move_candidates) if move_candidates else 'q'

        # AIの内部状態（行動履歴）を更新
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
        
        # 鍵を既に持っているならゴールへ向かう
        if player_info['keys']:
            return "GOAL_SEARCH"
        
        # 隠しアイテム探索
        if floor_info['hidden_items']:
            return "HIDDEN_ITEM_SEARCH"
        
        # ゴールに必要な鍵がなく，モンスターがいる場合は倒してドロップを狙う
        if floor_info['monsters']: 
            return "MONSTER_HUNT"
        
        return "GOAL_SEARCH"
    
    
    def _init_info_on_floor_change(self, floor_info: dict):
        """ フロア移動時に呼び出され，AIの内部記憶をそのフロア用に初期化する """
        # フロアID更新
        self.previous_floor_id = self.current_floor_id

        # 位置・方向情報初期化
        self.previous_position = (-1, -1)
        self.current_position = (-1, -1)
        self.previous_direction = ""
        self.current_direction = ""

        # ギミック情報初期化
        self.teleport_map = {}
        self._teleport(floor_info)  # テレポート情報の初期構築

        # 氷床情報の構築
        self.ice_regions = set()
        for gimmick in floor_info['gimmicks']:
            if gimmick['type'] == 'ice':
                self.ice_regions.update({tuple(pos) for pos in gimmick['positions']})
            elif gimmick['type'] == 'terrain_damage':
                pass  # 地形ダメージはコスト計算時に参照するためここでは保持しない

    # ===== teleportギミック関連 =====
    def _update_teleport_map_from_last_turn(self, floor_info: dict, player_info: dict) -> None:
        """
        直前ターンの行動結果から，テレポートのリンク情報を更新する．
            「位置Aから右へ移動」し，通常なら「位置B」に着くはずが，実際には「位置C」にいた場合，
            位置Bはテレポートマスであり，B -> C へリンクしていると判断できる．
        """
        if self.previous_position == (-1, -1):
            return

        last_action = self.current_direction
        if last_action not in DIRECTIONS:
            return

        # テレポートを考慮しないで移動した場合の到達点を計算
        # end_before_teleport: テレポート発動前の着地予想地点
        end_before_teleport, step_cost, _ = self.simulate_move(
            start_pos = self.previous_position, 
            move_dir = last_action, 
            floor_info = floor_info, 
            player_info = player_info, 
            consider_teleport = False  # テレポートしない前提で計算
        )
        if step_cost == self.INF:
            return

        # 予想地点がテレポートマップに登録されており，かつ実際の現在地と異なる場合
        # テレポートが発動したとみなし，リンク先を確定(confirm)させる
        if end_before_teleport in self.teleport_map and end_before_teleport != self.current_position:
            self.teleport_confirm(end_before_teleport, self.current_position)

    def _teleport(self, floor_info: dict):
        """
        フロアデータからテレポートマスの位置情報を初期化する．
        - テレポートマスが2マスのみである場合，双方向だと仮定して情報を登録する．
        - それ以外の場合はリンク関係が不明なため，位置のみ登録する．
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
        """ テレポートギミックのリンク情報を確定として記録する """
        self.teleport_map[source_pos] = {"target": target_pos, "confirmed": True}
    

    def teleport_suspect(self, source_pos: tuple[int, int], target_pos: tuple[int, int]):
        """ テレポートギミックのリンク情報を仮情報として記録する（現状未使用） """
        if source_pos in self.teleport_map and not self.teleport_map[source_pos]['confirmed']:
            self.teleport_map[source_pos] = {"target": target_pos, "confirmed": False}
    
    
    # 戦闘ダメージ予測
    def _estimate_monster_damage(self, strength: str = 'normal', player_atk: int = 10) -> int:
        """ プレイヤーの攻撃力とモンスターの強さから，プレイヤーの被ダメージを概算する """
        # 強さごとのステータス係数
        if strength == 'weak':
            monster_hp, m_atk = 30, 3  # ~0.3倍
        elif strength == 'normal':
            monster_hp, m_atk = 60, 6  # ~0.6倍
        elif strength == 'strong':
            monster_hp, m_atk = 100, 10 # ~1.0倍
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
        コスト = 基本移動コスト + 罠 + 地形ダメージ + モンスター戦闘ダメージ
            勝てないモンスターがいるマスは INF (通行不可) とする．
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
                    total_cost += self.BASE_TERRAIN_DAMAGE_COST
        
        # 3. モンスター戦闘コスト
        for monster in floor_info['monsters']:
            if tuple(monster['pos']) == position:
                damage = self._estimate_monster_damage(monster['strength'], player_info['attack'])
                
                # 「倒さないと通れない」かつ「負ける（HP以上のダメージ）」場合，通行不可
                if damage >= player_info['hp']:
                    if player_info['potions'] and damage < self.MAX_HP:
                        pass  # ポーションで回復して耐えられるなら通行可（コストは高い）
                    else:
                        return self.INF  # 絶対に勝てないなら通行不可
                
                total_cost += damage
                
        return total_cost

    # 経路探索
    def dijkstra(self, start_pos: tuple[int, int], targets: set[tuple[int, int]], floor_info: dict, player_info: dict) -> tuple[str, list[tuple[int, int]]]:
        """
        ダイクストラ法を用いてターゲットまでの最短（最小コスト）経路を探索する．
        Returns:
            first_move (str): 最適経路の最初の一手 ('w', 'a', 's', 'd')
            path (list): 経路となる座標のリスト
        """
        grid = floor_info['grid']
        
        # 優先度付きキュー: (累積コスト, 現在座標, 最初の一歩の方向, 経路)
        pq = [(0, start_pos, "", [start_pos])]
        
        # 訪問済みコスト管理: 座標 -> 最小コスト
        min_costs = {start_pos: 0}

        while pq:
            current_cost, current_pos, first_move, path = heapq.heappop(pq)
            
            # より低コストで到達済みならスキップ
            if current_cost > min_costs.get(current_pos, self.INF):
                continue
            
            # ターゲット到達判定
            if current_pos in targets:
                return first_move, path
            
            # 隣接ノード探索
            for move_dir in DIRECTIONS:
                # 移動シミュレーション (氷床やテレポートを考慮)
                next_pos, step_cost, traversed_positions = self.simulate_move(start_pos=current_pos, move_dir=move_dir, floor_info=floor_info, player_info=player_info)
                
                # 通行不可（勝ち目のないモンスターなど）の場合はスキップ
                if step_cost == self.INF:
                    continue
                
                new_cost = current_cost + step_cost
                next_first_move = first_move if first_move else move_dir  # 最初の一手を保持

                # 経路リストの更新
                new_path = path + traversed_positions
                if not new_path or next_pos != new_path[-1]:
                    new_path = new_path + [next_pos]

                # 特殊判定: 氷床滑り中の通過マスにターゲットがある場合  TODO: 最短経路を保証できていない．
                # 滑っている途中でもアイテム回収等は可能なため，通過経路上にターゲットがあれば到達とみなす
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
        ある位置からある方向へ1手移動した際の結果をシミュレーションする． 
        氷床による滑り移動や，テレポートによる位置飛びを考慮して最終到達点とコストを計算する．
        Args:
            consider_teleport (bool): テレポート処理を行うかどうか
        Returns:
            tuple: 到達座標, 移動コスト, 通過した座標リスト
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

        # 1歩目の移動確定とコスト計算
        current_pos = (next_r, next_c)
        total_cost = self.calculate_step_cost(position=current_pos, floor_info=floor_info, player_info=player_info)

        path_positions = [current_pos] # 通過座標リスト（氷滑り用）

        # Ice ギミック (滑り移動)
        # 現在地が氷なら，壁・ドア・氷以外のマスにぶつかるまで滑り続ける
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

                # 次のマスが有効なので移動
                current_pos = next_pos

                # 滑り中の通過マスのコストも加算する
                step_cost = self.calculate_step_cost(position=current_pos, floor_info=floor_info, player_info=player_info)
                total_cost += step_cost
                path_positions.append(current_pos)

                # 氷の領域から出たら停止
                if next_pos not in self.ice_regions:
                    break
        
        # Teleport ギミック
        # 到達点がテレポートマスであり，かつリンク先が判明している場合，座標を飛ばす
        if consider_teleport and current_pos in self.teleport_map and self.teleport_map[current_pos]['target'] != (-1, -1):
            current_pos = self.teleport_map[current_pos]['target']

        return current_pos, total_cost, path_positions
