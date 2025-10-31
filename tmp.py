# -*- coding: utf-8 -*-
import json
import random
from collections import deque

DIRECTIONS = {'w': (-1,0), 's': (1,0), 'a': (0,-1), 'd': (0,1)}

# ------------------------------------------------------------
# 軽量パース：grid用テキスト + infoセクションは json ファイル名のみ
# ------------------------------------------------------------
def load_grid_and_jsonpath(map_txt_path):
    """
    map_txt を読み、[grid] と [info] を最低限だけ処理する。
    - [grid] は # と . のみ（検証は最小限）
    - [info] は json=xxx.json だけを見る
    返り値: (grid: List[List[str]], json_path: str)
    """
    with open(map_txt_path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f]

    section = None
    grid = []
    json_path = None

    for s in lines:
        s = s.strip()
        if not s or s.startswith('//'):
            continue
        if s.startswith('[') and s.endswith(']'):
            section = s[1:-1].lower()
            continue

        if section == 'grid':
            # gridは#/.のみ（ざっくりチェック）
            assert all(ch in '#.' for ch in s), "gridは # / . のみ"
            grid.append(list(s))
        elif section == 'info':
            # 例: json=map06.json
            if s.startswith('json='):
                json_path = s.split('=', 1)[1].strip()

    if not grid:
        raise ValueError("gridが空です")
    if not json_path:
        raise ValueError("[info] に json=... が必要です")
    return grid, json_path

# ------------------------------------------------------------
# 必須クラス: Floor / GameState / Player
# ------------------------------------------------------------
class Floor:
    """
    1フロア分の全データ（grid以外はJSONから供給）
    grid: 2D list (# / .)
    以下はJSONで与える:
      name, reveal_hidden, start, goal, goal.type/keys
      items, monsters, doors, chests, teleports, gimmicks
    """
    def __init__(self, grid, meta):
        self.grid = grid                          # [['#','.','.',...], ...]
        self.name = meta.get('name', '')
        self.reveal_hidden = bool(meta.get('reveal_hidden', True))
        self.start = tuple(meta['start'])         # [r,c] を (r,c) に

        # --- ゴール ---
        goal = meta.get('goal', {})
        self.goal = {
            'type': goal.get('type', 'reach'),
            'reach': tuple(goal['reach']) if 'reach' in goal else None,
            'keys': list(goal.get('keys', [])),
        }

        # --- オーバーレイ ---
        # 形式は README の JSON スキーマ参照
        self.items = {it['id']: it for it in meta.get('items', [])}
        for it in self.items.values():
            it.setdefault('picked', False)
            it['pos'] = tuple(it['pos'])

        self.monsters = {m['id']: m for m in meta.get('monsters', [])}
        for m in self.monsters.values():
            m['pos'] = tuple(m['pos'])
            m.setdefault('alive', True)
            m.setdefault('turn', 0)     # 経過ターン
            # ステは入場時に自動設定する前提。なければここで簡易付与
            m.setdefault('hp', 30)
            m.setdefault('atk', 6)

        self.doors = {d['id']: d for d in meta.get('doors', [])}
        for d in self.doors.values():
            d['pos'] = tuple(d['pos'])
            d.setdefault('locked', True)

        self.chests = {c['id']: c for c in meta.get('chests', [])}
        for c in self.chests.values():
            c['pos'] = tuple(c['pos'])
            c.setdefault('opened', False)
            c.setdefault('contents', [])

        self.teleports = {t['id']: t for t in meta.get('teleports', [])}
        for t in self.teleports.values():
            t['src'] = tuple(t['src'])
            t['dst'] = tuple(t['dst'])
            t.setdefault('bi', False)

        # --- ギミック ---
        g = meta.get('gimmicks', {})
        self.gimmicks = {
            'ice': {tuple(p) for p in g.get('ice', [])},        # set((r,c),...)
            'hp_drain': int(g.get('hp_drain', 0)),
            'monster_ice': bool(g.get('monster_ice', True)),
            'trap_cells': {tuple(p) for p in g.get('trap_cells', [])},
        }

class Player:
    MAX_HP = 100
    BASE_ATK = 10
    def __init__(self, start):
        self.pos = start
        self.hp = Player.MAX_HP
        self.atk = Player.BASE_ATK
        self.keys = set()
        self.inv = {}  # id -> item(dict)

class GameState:
    """
    複数フロアの進行・描画・戦闘・移動・モブ行動などをまとめて面倒を見る。
    - 主要関数は極力このクラスのメソッドに集約。
    """
    def __init__(self, map_json_pairs):
        """
        map_json_pairs: [(map_txt_path, json_path_override_or_None), ...]
          - 通常は map_txt に書かれた json=... を使う。第二引数で上書き可。
        """
        self.floors = []
        for map_txt, override in map_json_pairs:
            grid, embedded_json = load_grid_and_jsonpath(map_txt)
            json_path = override or embedded_json
            with open(json_path, encoding='utf-8') as jf:
                meta = json.load(jf)
            self.floors.append(Floor(grid, meta))

        self.floor_idx = 0
        self.cleared_count = 0
        self.is_game_over = False
        self.is_game_cleared = False

        # プレイヤーは現在フロアの start に出現
        self.player = Player(self.current_floor().start)

    # ---------- 進行管理 ----------
    def current_floor(self):
        return self.floors[self.floor_idx]

    def go_next_floor(self):
        """ フロアクリア後に呼ぶ。5回クリアでゲームクリア """
        self.cleared_count += 1
        if self.cleared_count >= 5:
            self.is_game_cleared = True
            return
        self.floor_idx = min(self.floor_idx + 1, len(self.floors) - 1)
        # 新フロア入場時：位置・HP等は設計次第（ここでは位置のみ初期化）
        self.player.pos = self.current_floor().start

    # ---------- 描画 ----------
    def render(self):
        fl = self.current_floor()
        n, m = len(fl.grid), len(fl.grid[0])

        mons = {mobj['pos'] for mobj in fl.monsters.values() if mobj['alive']}
        doors_locked = {d['pos'] for d in fl.doors.values() if d['locked']}
        chests_closed = {c['pos'] for c in fl.chests.values() if not c['opened']}

        telepads = set()
        for tp in fl.teleports.values():
            telepads.add(tp['src'])
            if tp['bi']:
                telepads.add(tp['dst'])

        hidden_cells = set()
        if fl.reveal_hidden:
            for it in fl.items.values():
                if (not it.get('picked')) and it.get('hidden', False):
                    hidden_cells.add(it['pos'])

        for r in range(n):
            row = []
            for c in range(m):
                pos = (r,c)
                if fl.grid[r][c] == '#':
                    row.append('#'); continue
                # オーバーレイ優先度
                if self.player.pos == pos:
                    row.append('@')
                elif pos in mons:
                    row.append('M')
                elif pos in doors_locked:
                    row.append('D')
                elif pos in chests_closed:
                    row.append('C')
                elif pos in hidden_cells:
                    row.append('?')
                elif fl.goal.get('reach') and pos == fl.goal['reach']:
                    row.append('G')
                elif pos in telepads:
                    row.append('T')
                else:
                    row.append(' ')
            print("".join(row))
        print(f"HP:{self.player.hp}  ATK:{self.player.atk}  KEYS:{','.join(sorted(self.player.keys)) or '-'}")

    # ---------- 入出力 ----------
    def read_cmd(self):
        while True:
            cmd = input("(w/a/s/d 移動, u:ポーション, q:終了) > ").strip().lower()
            if cmd in ('w','a','s','d','u','q'):
                return cmd

    # ---------- 移動 ----------
    def try_move_player(self, dir_key):
        fl = self.current_floor()
        if dir_key not in DIRECTIONS:
            return None
        dr, dc = DIRECTIONS[dir_key]
        cur = self.player.pos
        nxt = (cur[0]+dr, cur[1]+dc)

        # 氷：出発 or 到達が氷でスライド
        if (cur in fl.gimmicks['ice']) or (nxt in fl.gimmicks['ice']):
            if not self._passable_for_player(nxt):
                return None
            return self._compute_slide_path(cur, (dr,dc))

        # 通常1歩
        if self._passable_for_player(nxt):
            return [nxt]
        return None

    def _compute_slide_path(self, start, delta):
        """ 氷上直進。壁/閉ドア/非氷に当たる直前で停止。通過セル列を返す """
        fl = self.current_floor()
        path = []
        r, c = start
        dr, dc = delta
        nxt = (r+dr, c+dc)
        if not self._passable_for_player(nxt):
            return path
        cur = nxt
        path.append(cur)
        while True:
            ahead = (cur[0]+dr, cur[1]+dc)
            if not self._in_bounds(ahead): break
            if self._is_wall(ahead): break
            if self._is_locked_door(ahead): break
            if ahead not in fl.gimmicks['ice']: break
            cur = ahead
            path.append(cur)
        return path

    # ---------- ステップ時の効果 ----------
    def on_step_common(self, path):
        """ 各セル通過時にHP減少/罠/アイテム/扉/宝箱/テレポを処理 """
        fl = self.current_floor()
        for i, pos in enumerate(path):
            # 1歩あたりHP減少
            if fl.gimmicks['hp_drain'] > 0:
                self.player.hp -= fl.gimmicks['hp_drain']
                if self.player.hp <= 0:
                    return

            # 地形罠（固定10）
            if pos in fl.gimmicks['trap_cells']:
                self.player.hp -= 10
                if self.player.hp <= 0:
                    return

            # アイテム
            for it in fl.items.values():
                if it.get('picked'): 
                    continue
                if tuple(it['pos']) != pos:
                    continue
                t = it['type']; prm = it.get('params', {})
                if t == 'trap':
                    dmg = int(prm.get('dmg', 10))
                    self.player.hp -= dmg
                    if int(prm.get('once', 1)):
                        it['picked'] = True
                    if self.player.hp <= 0:
                        return
                elif t == 'weapon':
                    self.player.atk += int(prm.get('atk', 0))
                    it['picked'] = True
                elif t == 'potion':
                    self.player.inv[it['id']] = it
                    it['picked'] = True
                elif t == 'key':
                    kid = prm.get('key_id')
                    if kid:
                        self.player.keys.add(kid)
                    it['picked'] = True

            # 扉/宝箱
            self._try_open_door(pos)
            self._try_open_chest(pos)

            # テレポ（停止時のみ発動）
            if i == len(path) - 1:
                for tp in fl.teleports.values():
                    if pos == tp['src']:
                        self.player.pos = tp['dst']; return
                    if tp.get('bi') and pos == tp['dst']:
                        self.player.pos = tp['src']; return

        if path:
            self.player.pos = path[-1]

    # ---------- 戦闘 ----------
    def battle_if_overlap(self):
        """ プレイヤー位置に敵がいれば戦闘を行う（プレイヤー先行・攻撃のみ） """
        m = self._monster_at(self.player.pos)
        if not m: 
            return True
        # ステは入場時自動設定が前提だが、無ければ簡易値がset済み
        while self.player.hp > 0 and m['hp'] > 0:
            m['hp'] -= self.player.atk
            if m['hp'] <= 0: break
            self.player.hp -= m['atk']
        if self.player.hp <= 0:
            return False
        m['alive'] = False
        # ドロップ
        for tok in m.get('drop', []):
            self._spawn_drop(tok, self.player.pos)
        return True

    # ---------- 敵ターン ----------
    def monsters_act(self):
        fl = self.current_floor()
        occupied = {m['pos'] for m in fl.monsters.values() if m['alive']}
        for m in fl.monsters.values():
            if not m['alive']:
                continue
            m['turn'] += 1
            mv = int(m.get('move', 1))
            if mv and (m['turn'] % mv != 0):
                continue

            ai = m.get('ai', 'static')
            prm = m.get('params', {})
            target = None

            if ai == 'static':
                pass
            elif ai == 'random':
                if random.random() < float(prm.get('p', 0.5)):
                    cand = []
                    for dr, dc in DIRECTIONS.values():
                        nx = (m['pos'][0]+dr, m['pos'][1]+dc)
                        if self._passable_for_monster(nx) and nx not in occupied:
                            cand.append(nx)
                    if cand: target = random.choice(cand)
            elif ai == 'chase':
                rng = int(prm.get('range', 6))
                dist = abs(m['pos'][0]-self.player.pos[0]) + abs(m['pos'][1]-self.player.pos[1])
                if dist <= rng:
                    step = self._bfs_next_step(m['pos'], self.player.pos)
                    if step and step not in occupied:
                        target = step
            elif ai == 'patrol':
                path = prm.get('path', [])
                if path:
                    # path は [[r,c], ...] で来る想定 → tuple化して扱う
                    path = [tuple(p) for p in path]
                    idx = prm.get('idx', 0)
                    dst = path[(idx + 1) % len(path)]
                    step = self._bfs_next_step(m['pos'], dst)
                    if step and step not in occupied:
                        target = step
                        if step == dst:
                            prm['idx'] = (idx + 1) % len(path)

            if target:
                occupied.discard(m['pos'])
                m['pos'] = target
                occupied.add(m['pos'])

            # 衝突で戦闘
            if m['alive'] and m['pos'] == self.player.pos:
                if not self.battle_if_overlap():
                    return False
        return True

    # ---------- フロア/ゲーム判定 ----------
    def reached_goal(self):
        fl = self.current_floor()
        t = fl.goal['type']
        if t == 'reach':
            return fl.goal['reach'] and self.player.pos == fl.goal['reach']
        elif t == 'keys_only':
            return set(fl.goal['keys']).issubset(self.player.keys)
        elif t == 'reach_and_keys':
            return (fl.goal['reach'] and self.player.pos == fl.goal['reach']) and set(fl.goal['keys']).issubset(self.player.keys)
        return False

    def use_potion(self):
        for k, it in list(self.player.inv.items()):
            if it['type'] == 'potion':
                self.player.hp = Player.MAX_HP
                del self.player.inv[k]
                return True
        return False

    # ---------- 1ターン（プレイヤー入力→結果→敵行動→判定） ----------
    def step_turn(self, cmd):
        if cmd == 'q':
            self.is_game_over = True
            return
        if cmd == 'u':
            print("Potion used." if self.use_potion() else "No potion.")
            return

        path = self.try_move_player(cmd)
        if not path:
            print("Cannot move.")
            return
        self.on_step_common(path)
        if self.player.hp <= 0:
            self.is_game_over = True
            return
        if not self.battle_if_overlap():
            self.is_game_over = True
            return
        if not self.monsters_act():
            self.is_game_over = True
            return
        if self.player.hp <= 0:
            self.is_game_over = True
            return
        if self.reached_goal():
            print("FLOOR CLEAR!")
            self.go_next_floor()
            if self.is_game_cleared:
                print("GAME CLEARED!")
                self.is_game_over = True

    # ---------- 内部ユーティリティ（判定/探索/ドロップ/操作） ----------
    def _in_bounds(self, pos):
        fl = self.current_floor()
        r, c = pos
        return 0 <= r < len(fl.grid) and 0 <= c < len(fl.grid[0])

    def _is_wall(self, pos):
        fl = self.current_floor()
        return fl.grid[pos[0]][pos[1]] == '#'

    def _is_locked_door(self, pos):
        fl = self.current_floor()
        for d in fl.doors.values():
            if d['locked'] and tuple(d['pos']) == pos:
                return True
        return False

    def _passable_for_player(self, pos):
        if not self._in_bounds(pos): return False
        if self._is_wall(pos): return False
        if self._is_locked_door(pos): return False
        return True

    def _passable_for_monster(self, pos):
        fl = self.current_floor()
        if not self._in_bounds(pos): return False
        if self._is_wall(pos): return False
        if self._is_locked_door(pos): return False
        if (pos in fl.gimmicks['ice']) and (not fl.gimmicks['monster_ice']):
            return False
        return True

    def _monster_at(self, pos):
        fl = self.current_floor()
        for m in fl.monsters.values():
            if m['alive'] and tuple(m['pos']) == pos:
                return m
        return None

    def _bfs_next_step(self, src, dst):
        fl = self.current_floor()
        q = deque([src])
        parent = {src: None}
        while q:
            cur = q.popleft()
            if cur == dst:
                break
            for dr, dc in DIRECTIONS.values():
                nx = (cur[0]+dr, cur[1]+dc)
                if nx in parent: 
                    continue
                if self._passable_for_monster(nx):
                    parent[nx] = cur
                    q.append(nx)
        if dst not in parent:
            return None
        cur = dst
        while parent[cur] and parent[cur] != src:
            cur = parent[cur]
        return cur

    def _spawn_drop(self, token, pos):
        fl = self.current_floor()
        # 'gen:weapon:+3' / 'gen:potion' / 'gen:key:red' / 既存item_id
        if token.startswith('gen:'):
            parts = token.split(':')
            kind = parts[1]
            new_id = f"DROP_{kind}_{random.randint(1000,9999)}"
            if kind == 'weapon':
                add = int(parts[2]) if len(parts) > 2 else 1
                fl.items[new_id] = {'id': new_id, 'type': 'weapon', 'pos': pos,
                                    'hidden': False, 'picked': False,
                                    'params': {'atk': add}}
            elif kind == 'potion':
                fl.items[new_id] = {'id': new_id, 'type': 'potion', 'pos': pos,
                                    'hidden': False, 'picked': False,
                                    'params': {}}
            elif kind == 'key':
                kid = parts[2] if len(parts) > 2 else 'generic'
                fl.items[new_id] = {'id': new_id, 'type': 'key', 'pos': pos,
                                    'hidden': False, 'picked': False,
                                    'params': {'key_id': kid}}
        else:
            if token in fl.items:
                it = fl.items[token]
                it['pos'] = pos
                it['hidden'] = False
                it['picked'] = False

    def _try_open_door(self, pos):
        fl = self.current_floor()
        for d in fl.doors.values():
            if tuple(d['pos']) == pos and d['locked']:
                need = d.get('key')
                if (need is None) or (need in self.player.keys):
                    d['locked'] = False
                    return True
        return False

    def _try_open_chest(self, pos):
        fl = self.current_floor()
        for ch in fl.chests.values():
            if tuple(ch['pos']) == pos and not ch['opened']:
                need = ch.get('key')
                if (need is None) or (need in self.player.keys):
                    ch['opened'] = True
                    for tok in ch.get('contents', []):
                        self._spawn_drop(tok, pos)
                    return True
        return False

# ------------------------------------------------------------
# 最小のゲームループ（例）
# ------------------------------------------------------------
def run(map_json_pairs):
    gs = GameState(map_json_pairs)
    while not gs.is_game_over:
        gs.render()
        cmd = gs.read_cmd()
        gs.step_turn(cmd)

# 例:
# run([
#   ("maps/map01.txt", None),
#   ("maps/map02.txt", None),
#   ("maps/map03.txt", None),
# ])

if __name__ == "__main__":
    run([("map_data/sample01.txt", None)])