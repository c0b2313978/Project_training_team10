# MazeRPG – Map/JSON 仕様 & 実行手順

本プロジェクトは **grid（地形）をテキスト**, **オブジェクト/ギミック等は JSON** に分離した構成です。  

## ディレクトリ構成

```
.
├── README.md
├── TODO.md
├── main.py                   # 実行エントリ
├── modules                   # ゲームロジック一式
│   ├── constants.py
│   ├── floor.py
│   ├── game_state.py
│   ├── items.py
│   ├── monsters.py
│   ├── objects.py
│   ├── player.py
│   └── read_map_data.py
├── game_texts
│   ├── Basic_rule.txt
│   ├── Controls_guide.txt
│   ├── Firstgame_ui.txt
│   ├── Floor_rule.txt
│   └── Opening.txt
└── map_data
    ├── map01.txt
    ├── map01.json
    ├── map02.txt
    ├── map02.json
    ├── ...
    ├── sample01.txt
    ├── sample01.json
    └── ...

```

---

## マップ（TXT）

`[grid]` と `[info]` セクションのみを使用します。

- **[grid]**: `#`=壁, `.`=床 のみ。矩形で揃えてください。
- **[info]**: `json=ファイルパス` の1行だけ（相対パス推奨）。

```ini
[grid]
#######
#.....#
#.#...#
#.....#
#######

[info]
json=maps/map01.json
````

---

## JSON スキーマ

トップレベルのキー：

| key             | 型             | 必須           | 説明                |
| --------------- | ------------- | ------------ | ----------------- |
| `name`          | string        | 任意           | フロア名              |
| `reveal_hidden` | boolean       | 任意(既定: true) | 隠しアイテムは `?` で描画   |
| `start`         | [int,int]     | 必須           | プレイヤー開始座標 `(r,c)` |
| `goal`          | object        | 任意           | ゴール条件（下記）         |
| `items`         | array<object> | 任意           | アイテム/置き罠          |
| `monsters`      | array<object> | 任意           | モンスター             |
| `doors`         | array<object> | 任意           | ドア（鍵で開く障害）        |
| `chests`        | array<object> | 任意           | 宝箱（中身スポーン）        |
| `teleports`     | array<object> | 任意           | テレポータ             |
| `gimmicks`      | object        | 任意           | 氷やHP減少などのギミック     |

### goal

```json
"goal": {
  "type": "reach" | "keys_only" | "reach_and_keys",
  "multiple": false | true  // 複数のゴール. trueの場合 pos が2次元リストで渡される
  "pos": [r,c],   // type=reach または reach_and_keys で使用
  "keys": ["gold","red"]  // ゴールに必要な key の id. type=keys_only または reach_and_keys で使用
}
```

### items

```json
{"id":"W1","type":"weapon","pos":[1,2],"hidden":false,"params":{"atk":5}}
{"id":"P1","type":"potion","pos":[1,5],"hidden":true,"params":{}}
{"id":"K1","type":"key","pos":[2,6],"hidden":false}
{"id":"TR1","type":"trap","pos":[3,4],"hidden":false,"params":{"damage":10,"once":1}}
```

* `weapon`: 取得即 `ATK += atk`。指定しない場合 `1~10` でランダム。
* `potion`: インベントリに入る。`u` で使用→HP全快
* `key`: `id` をプレイヤーが所持
* `trap`: 踏むと `damage` ダメージ。`once=1` なら一度きり。

### monsters

```json
{"id":"M1","pos":[2,8],"ai_type":"static","move_every":0,"drop_list":["P1"]}
{"id":"M2","pos":[6,4],"ai_type":"random","ai_params":{"p":0.5},"move":1,"drop_list":[{"id": "hoge", "type": "key", "params": {}}]}
{"id":"M3","pos":[8,6],"ai_type":"chase","ai_params":{"range":6},"move":1}
{"id":"M4","pos":[10,11],"ai_type":"patrol","ai_params":{"path":[[10,11],[10,15],[8,15],[8,11]]},"move_every":2}
```

* `ai_type`: `static` / `random` / `chase` / `patrol`
* `move_every`: 何ターンごとに移動するか（0=動かない）
* `ai_params`:

  * `random`: `{ "p": 0.5 }` 移動確率
  * `chase`: `{ "range": 6 }` 追跡開始距離
  * `patrol`: `{ "path": [[r,c], ...] }` 巡回点
* `strength`: `'weak'` | `'normal'` | `'strong'`
* `drop_list`: 撃破時ドロップ。 `items` の書き方と同じ

> HP/ATK は**フロア入場時に自動設定**前提（実装側で難易度係数をかける等）。サンプル実装では未指定時に簡易値 `(hp=30, atk=6)` を補完。

### doors

```json
{"id":"Dgold","pos":[10,15],"requires_key":"gold","opened":false}
```

* 同セルに入ると自動で解錠を試みる（鍵条件を満たす場合のみ）。

### chests

```json
{"id":"C1","pos":[5,6],"requires_key":"red","opened":false,"contents":["generate:weapon:+7","P1"]}
```

* 同セルに入ると自動で開封を試みる。中身はセル上にスポーン。

### teleports

```json
{"id":"T1","source":[7,12],"target":[3,2],"bidirectional":true}
```

* 通過時に起動（双方向は `bidirectional: true`）。
* 鍵が必要な時は `requires_key: {key_id}`。

### gimmicks

```json
{
  "ice": {"regions": []},                    // 氷セル（直進）, リストが空の場合はマップ全域
  "terrain_damage": {"damage": 1, "regions": []}  // 地形罠
}
```

---

## ゲームループと操作

* 5フロアクリアでゲームクリア（`GameState.go_next_floor()` 内で判定）
* コマンド: **w/a/s/d** 移動, **u** ポーション使用, **q** 終了
* 描画優先: **プレイヤー > モンスター > ドア(閉) > チェスト(未開) > 隠しアイテム(?) > ゴール > テレポ > 床**
  隠しアイテムは `reveal_hidden=true` のとき `?` で表示（踏むと正体判明/取得）

---

```
@ ←プレイヤー
M ←モンスター
D ←閉じたドア
C ←未開宝箱
? ←隠しアイテム（reveal_hidden=true の場合）
G ←ゴール地点
T ←テレポ台
```

---

## ゲーム要件
- k層あるマップのうち5層クリアでゲームクリア。
  - ゲーム開始時にk層のうちランダムに5種類選ばれる。
- 各層は基本的に n * m サイズの迷路状である。
- プレイヤーは一マスずつ移動する。
- 各層によって異なるギミックがある（同一のギミックがあることもある）。
  - 壁にぶつかるまで直進し続ける。
  - 一度通った道が使えなくなる。
  - 1マス進むごとにHPが減少していく。
  - 特定のマスを通るとマップ上の別の場所に移動する。
- プレイヤーの初期ステータス: HP100, Attack10
- HPが0になるとゲームオーバー（敗北）となる。
- マップ内にモンスターがいることがある。
	- モンスターのいるマスに重なると、HPが0になるまでプレイヤーとモンスターの間でターン制の戦闘が発生する。
	- プレイヤー先行で、プレイヤーおよびモンスターは攻撃のみ可能である。
  - モンスターを倒すことで入手すことができるアイテムなどがある。
  - モンスターの挙動は階層ごとに異なる（不動、巡回、追跡、など）。
- マップ内にはアイテムが設置してあることがある。プレイヤーがアイテムや罠のあるマスに重なることでアイテムの効果が取得（反映）される。
	- 武器: プレイやの攻撃力が上昇する。取得時に即時反映される。
	- ポーション: 取得時インベントリに追加される。任意のタイミングで使用可能。プレイヤーのHPをプレイヤーの最大HPまで回復させる。
	- 鍵: マップゴールに必要であったり、マップ内に存在する宝箱を開けるのに必要であったりする。
	- 罠: プレイヤーに10のダメージを与える。即時反映される。
  - 宝箱: 特定の鍵を所持した状態のときに開けることができる。何らかのアイテムを入手することができる。

---

## modules ディレクトリ内ファイル概要
- `constants.py`: フロア選択数や総フロア数、移動ベクトル`DIRECTIONS`、描画記号`TILE_SYMBOLS`、データパスなどの共通定数をまとめる。
- `read_map_data.py`: マップの`.txt`を読み込み、`[grid]`と`[info]`を分離して`grid`と`json_path`を返すユーティリティ。
- `floor.py`: フロア1層分のモデル。`Floor`初期化時に`read_map_data`→JSON読み込みで`Item/Monster/Door/Chest/Teleport/Gimmicks`を生成。`print_grid`で描画、`enter_cell`でアイテム・ギミック・テレポ処理、`battle_monster`でターン制戦闘とドロップ生成、`check_goal`でゴール判定を担当。
- `game_state.py`: ゲーム全体の進行管理。フロア選択や`start_floor`で`Floor`生成、`step_turn`で入力→移動→`Floor.enter_cell`→モンスター行動→戦闘→`check_goal`を実行し、`next_floor`で進行を進める。`try_move_player`など入出力補助もここにある。
- `items.py`: アイテム階層。`Item`を基底に`Key/Weapon/Potion/Trap/Dummy`を用意し、`create_item`ファクトリでJSON定義から適切なクラスを生成。`Weapon.apply_effect`は`Player.equip_weapon`を呼び攻撃力を上げ、`Potion`/`Trap`はHPを直接回復・減少させる。
- `monsters.py`: `Monster`クラス。`init_status`で強さ係数からHP/攻撃力を決め、`increment_turn`で移動周期管理、`monster_next_move`で`static/random/chase/patrol`AIを切替、`bfs`で追跡経路を計算。`drop_list`は`Floor.battle_monster`経由で`Item`生成に使われる。
- `objects.py`: マップ上の構造物とギミック。`Door`/`Chest`/`Teleport`は位置と鍵条件を保持し、`Teleport.get_destination`がプレイヤー位置を転送。`Gimmicks`は氷床・地形ダメージ領域を管理し、`ice_gimmick_effect`で連続滑走と訪問セル追加、`apply_terrain_damage`で`Player.hp`を減少させる。
- `player.py`: `Player`クラス。位置・HP・攻撃力・所持品を管理し、`add_item`でインベントリ格納、`use_potion`で全回復、`equip_weapon`で最良武器を装備し攻撃力を再計算、`floor_clear_keys_reset`でフロア跨ぎの鍵をリセットする。

## クラス間の主な影響関係 (mermaid)
```mermaid
flowchart TB
  main["main.py<br>main()"] --> gsInit["GameState.__init__<br>フロア抽選 + Player生成"]
  gsInit --> floorInit["GameState.start_floor<br>Floor(...) 作成"]
  floorInit --> floorLoad["Floor.__init__<br>read_map_data + JSON読込"]
  floorLoad --> comp["Item / Monster / Door / Chest / Teleport / Gimmicks<br>各クラスを初期化"]
  gsInit --> loop["GameState.step_turn<br>(ゲームループ)"]
  loop --> render["Floor.print_grid +<br>Player.print_status"]
  loop --> move["try_move_player<br>-> Player.position / last_move_direction"]
  move --> enterCell["Floor.enter_cell"]
  enterCell --> items["Item.create_item 派生<br>apply_effect / Player.add_item"]
  items --> player["Player<br>hp・attack・inventory更新<br>equip_weapon / use_potion"]
  enterCell --> gimmicks["Gimmicks<br>ice_gimmick_effect / apply_terrain_damage"]
  gimmicks --> player
  enterCell --> teleDoor["Teleport / Door / Chest<br>get_destination, opened 判定"]
  teleDoor --> player
  loop --> monsters["Monster.increment_turn<br>monster_next_move (BFS)"]
  monsters --> monsterState["Monster.pos / alive / drop_list"]
  monsterState --> battle["Floor.battle_monster<br>ターン制ダメージ"]
  battle --> player
  battle --> drops["Monster.drop_list<br>Item.create_item -> Player.add_item"]
  drops --> player
  loop --> goal["Floor.check_goal<br>Player.position + Player.keys"]
  goal -->|達成| next["GameState.next_floor<br>Player.floor_clear_keys_reset"]
  next --> gsInit
  player --> status["GameState.check_game_over<br>/ check_game_cleared"]
  status --> loop
```

## ゲーム全体フロー (mermaid)
```mermaid
flowchart TD
  start([Game Start]) --> init["GameState.__init__<br>フロア抽選 / Player()"]
  init --> opening["print_all_opening<br>+ Floor.rule 表示"]
  opening --> loop{GameState.game_state?<br>step_turn継続}
  loop --> step["GameState.step_turn 実行"]
  step --> input{"入力 w/a/s/d/u/r/q"}
  input -->|q| quit["is_game_over = True"]
  input -->|u| potion["Player.use_potion()<br>HP=MAX"] --> statusCheck["check_game_over / cleared"]
  input -->|r| showRule["Floor.rule 再表示"] --> statusCheck
  input -->|w/a/s/d| moveTry["try_move_player<br>壁・範囲チェック"]
  moveTry -->|不可| input
  moveTry -->|成功| enterFlow["Floor.enter_cell<br>items / gimmick / teleport"]
  enterFlow --> monsterPhase["各 Monster.increment_turn<br>monster_next_move"]
  monsterPhase --> battle["Floor.battle_monster<br>衝突時に開始"]
  battle --> playerState["Player.hp / inventory 更新"]
  enterFlow --> playerState
  playerState --> goalCheck{"Floor.check_goal"}
  goalCheck -->|未達| statusCheck
  goalCheck -->|達成| nextFloor["GameState.next_floor<br>start_floor + Player.reset"]
  nextFloor --> opening
  statusCheck -->|継続| loop
  statusCheck -->|ゲームオーバー| endGame([Game Over])
  goalCheck -->|全フロア完了| clear(["print_game_text(Ending)<br>ゲームクリア"])
  quit --> endGame
```

## クラス別メンバーと矢印対応 (mermaid)
メソッドとインスタンス変数を個別ノード化し、主な作用先を矢印で表現しています。各クラスは色分けしています。

```mermaid
graph LR
  %% GameState
  subgraph GameState
    GS_is["var is_game_state"]
    GS_req["var requires_map_file_path"]
    GS_floors["var all_floors"]
    GS_clear["var cleared_count"]
    GS_idx["var current_floor_index"]
    GS_over["var is_game_over"]
    GS_cleared["var is_game_cleared"]
    GS_floor["var floor (Floor)"]
    GS_player["var player (Player)"]
    GS_init["method __init__"]
    GS_game["method game_state"]
    GS_start["method start_floor"]
    GS_next["method next_floor"]
    GS_chk_over["method check_game_over"]
    GS_chk_clear["method check_game_cleared"]
    GS_read["method read_command"]
    GS_step["method step_turn"]
  end

  %% Floor
  subgraph Floor
    FL_id["var floor_id"]
    FL_grid["var grid"]
    FL_json["var json_path"]
    FL_map["var map_size"]
    FL_move["var movable_cells"]
    FL_info["var info"]
    FL_name["var name"]
    FL_reveal["var reveal_hidden"]
    FL_start["var start"]
    FL_goal_type["var goal.type"]
    FL_goal_pos["var goal.pos"]
    FL_goal_keys["var goal.keys"]
    FL_items["var items dict"]
    FL_monsters["var monsters dict"]
    FL_doors["var doors dict"]
    FL_chests["var chests dict"]
    FL_tp["var teleports dict"]
    FL_gimmicks["var gimmicks"]
    FL_rule["var rule"]
    FL_ctor["method __init__"]
    FL_read["method _read_json_data"]
    FL_goal_init["method _goal_init"]
    FL_items_init["method _items_init"]
    FL_mons_init["method _monsters_init"]
    FL_doors_init["method _doors_init"]
    FL_chests_init["method _chests_init"]
    FL_tp_init["method _teleports_init"]
    FL_gimmicks_init["method _gimmicks_init"]
    FL_rule_init["method _rules_init"]
    FL_print_info["method print_info"]
    FL_collect["method _collect_entity_symbols"]
    FL_print["method print_grid"]
    FL_handle["method _handle_cell_items"]
    FL_enter["method enter_cell"]
    FL_battle["method battle_monster"]
    FL_goal_chk["method check_goal"]
  end

  %% Player
  subgraph Player
    PL_pos["var position"]
    PL_hp["var hp"]
    PL_attack["var attack"]
    PL_eq_id["var equipped_weapon_id"]
    PL_eq_atk["var equipped_weapon_attack"]
    PL_inv["var inventory dict"]
    PL_keys["var keys set"]
    PL_pots["var potions set"]
    PL_last["var last_move_direction"]
    PL_print["method print_status"]
    PL_inv_print["method print_inventory"]
    PL_add["method add_item"]
    PL_reset_keys["method floor_clear_keys_reset"]
    PL_use["method use_potion"]
    PL_recalc["method recalculate_attack"]
    PL_equip["method equip_weapon"]
    PL_org["method item_organizing"]
  end

  %% Monster
  subgraph Monster
    MON_id["var id"]
    MON_pos["var pos"]
    MON_next_pos["var next_pos"]
    MON_ai["var ai_type"]
    MON_ai_param["var ai_params"]
    MON_move_every["var move_every"]
    MON_turn["var turn_counter"]
    MON_drop["var drop_list"]
    MON_strength["var strength"]
    MON_alive["var alive"]
    MON_hp["var hp"]
    MON_attack["var attack"]
    MON_patrol_points["var patrol_points"]
    MON_patrol_idx["var patrol_point"]
    MON_debug["var debug_path"]
    MON_ctor["method __init__"]
    MON_status["method init_status"]
    MON_incr["method increment_turn"]
    MON_reset["method reset_turn_counter"]
    MON_move["method monster_next_move"]
    MON_bfs["method bfs"]
  end

  %% Items (generic + subclasses)
  subgraph Items
    IT_id["var id"]
    IT_type["var type"]
    IT_pos["var pos"]
    IT_hidden["var hidden"]
    IT_params["var params"]
    IT_picked["var picked"]
    IT_create["method create_item"]
    IT_apply["method Item.apply_effect"]
    KEY_apply["method Key.apply_effect"]
    WPN_apply["method Weapon.apply_effect"]
    POT_apply["method Potion.apply_effect"]
    TRP_apply["method Trap.apply_effect"]
    DMY_apply["method Dummy.apply_effect"]
  end

  %% Objects / Gimmicks
  subgraph Objects
    DR_id["var Door.id"]
    DR_pos["var Door.pos"]
    DR_req["var Door.requires_key"]
    DR_open["var Door.opened"]
    CH_id["var Chest.id"]
    CH_pos["var Chest.pos"]
    CH_req["var Chest.requires_key"]
    CH_cont["var Chest.contents"]
    CH_open["var Chest.opened"]
    TP_id["var Teleport.id"]
    TP_src["var Teleport.source"]
    TP_tgt["var Teleport.target"]
    TP_req["var Teleport.requires_key"]
    TP_bi["var Teleport.bidirectional"]
    GM_grid["var Gimmicks.grid"]
    GM_cells["var Gimmicks.moveable_cells"]
    GM_params["var Gimmicks.params"]
    GM_ice["var ice_regions"]
    GM_terrain["var terrain_damage_regions"]
    GM_damage["var terrain_damage"]
    CH_return["method Chest.return_contents"]
    TP_dest["method Teleport.get_destination"]
    GM_norm["method Gimmicks._normalize_region_list"]
    GM_is["method is_gimmick_cell / is_ice_cell"]
    GM_ice_eff["method ice_gimmick_effect"]
    GM_terrain_val["method terrain_damage_value"]
    GM_apply_damage["method apply_terrain_damage"]
  end

  %% Edge definitions (GameState)
  GS_init --> GS_req
  GS_init --> GS_floors
  GS_init --> GS_floor
  GS_init --> GS_player
  GS_init --> GS_clear
  GS_init --> GS_idx
  GS_init --> GS_is
  GS_game --> GS_is
  GS_start --> GS_floor
  GS_start --> FL_ctor
  GS_next --> GS_clear
  GS_next --> GS_idx
  GS_next --> GS_cleared
  GS_next --> PL_reset_keys
  GS_chk_over --> GS_over
  GS_chk_over --> PL_hp
  GS_chk_clear --> GS_cleared
  GS_step --> PL_pos
  GS_step --> PL_last
  GS_step --> FL_print
  GS_step --> FL_enter
  GS_step --> MON_incr
  GS_step --> MON_move
  GS_step --> FL_battle
  GS_step --> FL_goal_chk
  GS_step --> GS_next
  GS_step --> GS_chk_over
  GS_step --> GS_chk_clear

  %% Floor edges
  FL_ctor --> FL_id
  FL_ctor --> FL_grid
  FL_ctor --> FL_json
  FL_ctor --> FL_map
  FL_ctor --> FL_move
  FL_ctor --> FL_info
  FL_ctor --> FL_name
  FL_ctor --> FL_reveal
  FL_ctor --> FL_start
  FL_ctor --> FL_rule
  FL_ctor --> FL_goal_init
  FL_ctor --> FL_items_init
  FL_ctor --> FL_mons_init
  FL_ctor --> FL_doors_init
  FL_ctor --> FL_chests_init
  FL_ctor --> FL_tp_init
  FL_ctor --> FL_gimmicks_init
  FL_goal_init --> FL_goal_type
  FL_goal_init --> FL_goal_pos
  FL_goal_init --> FL_goal_keys
  FL_items_init --> FL_items
  FL_mons_init --> FL_monsters
  FL_doors_init --> FL_doors
  FL_chests_init --> FL_chests
  FL_tp_init --> FL_tp
  FL_gimmicks_init --> FL_gimmicks
  FL_rule_init --> FL_rule
  FL_handle --> FL_items
  FL_handle --> IT_picked
  FL_handle --> IT_apply
  FL_handle --> PL_inv
  FL_handle --> PL_keys
  FL_handle --> PL_pots
  FL_enter --> FL_handle
  FL_enter --> GM_ice_eff
  FL_enter --> GM_apply_damage
  FL_enter --> TP_dest
  FL_enter --> PL_pos
  FL_enter --> PL_hp
  FL_battle --> MON_hp
  FL_battle --> MON_alive
  FL_battle --> MON_drop
  FL_battle --> PL_hp
  FL_battle --> PL_inv
  FL_battle --> IT_create
  FL_battle --> IT_apply
  FL_goal_chk --> FL_goal_pos
  FL_goal_chk --> FL_goal_keys
  FL_goal_chk --> PL_pos
  FL_goal_chk --> PL_inv

  %% Player edges
  PL_print --> PL_hp
  PL_print --> PL_attack
  PL_inv_print --> PL_inv
  PL_add --> PL_inv
  PL_add --> PL_keys
  PL_add --> PL_pots
  PL_reset_keys --> PL_keys
  PL_reset_keys --> PL_inv
  PL_use --> PL_pots
  PL_use --> PL_inv
  PL_use --> PL_hp
  PL_recalc --> PL_attack
  PL_equip --> PL_eq_id
  PL_equip --> PL_eq_atk
  PL_equip --> PL_attack
  PL_org --> PL_inv

  %% Monster edges
  MON_ctor --> MON_id
  MON_ctor --> MON_pos
  MON_ctor --> MON_ai
  MON_ctor --> MON_ai_param
  MON_ctor --> MON_move_every
  MON_ctor --> MON_drop
  MON_ctor --> MON_strength
  MON_ctor --> MON_status
  MON_status --> MON_hp
  MON_status --> MON_attack
  MON_status --> MON_patrol_points
  MON_status --> MON_patrol_idx
  MON_incr --> MON_turn
  MON_reset --> MON_turn
  MON_move --> MON_pos
  MON_move --> MON_next_pos
  MON_bfs --> MON_debug

  %% Item edges
  IT_create --> IT_id
  IT_create --> IT_type
  IT_create --> IT_pos
  IT_create --> IT_hidden
  IT_create --> IT_params
  WPN_apply --> PL_equip
  POT_apply --> PL_hp
  TRP_apply --> PL_hp
  KEY_apply --> PL_keys
  IT_apply --> PL_inv

  %% Object edges
  CH_return --> IT_create
  TP_dest --> PL_pos
  GM_ice_eff --> PL_pos
  GM_apply_damage --> PL_hp
  GM_norm --> GM_ice
  GM_norm --> GM_terrain

  %% Cross links
  GS_floor --> FL_ctor
  GS_player --> PL_pos
  GS_next --> GS_floor
  GS_next --> GS_player
  FL_monsters --> MON_ctor
  FL_items --> IT_create
  FL_tp --> TP_dest
  FL_gimmicks --> GM_ice_eff
  FL_gimmicks --> GM_apply_damage
  PL_attack --> MON_hp
  MON_attack --> PL_hp

  classDef gamestate fill:#fde4ec,stroke:#c2185b,color:#000;
  classDef floor fill:#fff8e1,stroke:#ff6f00,color:#000;
  classDef player fill:#e3f2fd,stroke:#1565c0,color:#000;
  classDef monster fill:#ede7f6,stroke:#5e35b1,color:#000;
  classDef items fill:#f1f8e9,stroke:#558b2f,color:#000;
  classDef objects fill:#fbe9e7,stroke:#e64a19,color:#000;

  class GS_is,GS_req,GS_floors,GS_clear,GS_idx,GS_over,GS_cleared,GS_floor,GS_player,GS_init,GS_game,GS_start,GS_next,GS_chk_over,GS_chk_clear,GS_read,GS_step gamestate;
  class FL_id,FL_grid,FL_json,FL_map,FL_move,FL_info,FL_name,FL_reveal,FL_start,FL_goal_type,FL_goal_pos,FL_goal_keys,FL_items,FL_monsters,FL_doors,FL_chests,FL_tp,FL_gimmicks,FL_rule,FL_ctor,FL_read,FL_goal_init,FL_items_init,FL_mons_init,FL_doors_init,FL_chests_init,FL_tp_init,FL_gimmicks_init,FL_rule_init,FL_print_info,FL_collect,FL_print,FL_handle,FL_enter,FL_battle,FL_goal_chk floor;
  class PL_pos,PL_hp,PL_attack,PL_eq_id,PL_eq_atk,PL_inv,PL_keys,PL_pots,PL_last,PL_print,PL_inv_print,PL_add,PL_reset_keys,PL_use,PL_recalc,PL_equip,PL_org player;
  class MON_id,MON_pos,MON_next_pos,MON_ai,MON_ai_param,MON_move_every,MON_turn,MON_drop,MON_strength,MON_alive,MON_hp,MON_attack,MON_patrol_points,MON_patrol_idx,MON_debug,MON_ctor,MON_status,MON_incr,MON_reset,MON_move,MON_bfs monster;
  class IT_id,IT_type,IT_pos,IT_hidden,IT_params,IT_picked,IT_create,IT_apply,KEY_apply,WPN_apply,POT_apply,TRP_apply,DMY_apply items;
  class DR_id,DR_pos,DR_req,DR_open,CH_id,CH_pos,CH_req,CH_cont,CH_open,TP_id,TP_src,TP_tgt,TP_req,TP_bi,GM_grid,GM_cells,GM_params,GM_ice,GM_terrain,GM_damage,CH_return,TP_dest,GM_norm,GM_is,GM_ice_eff,GM_terrain_val,GM_apply_damage objects;
```

矢印は「左ノードのメソッドが右ノードの変数や他メソッドに作用する」ことを示します。色は GameState=ピンク、Floor=黄、Player=水色、Monster=紫、Items=緑、Objects/Gimmicks=オレンジです。



