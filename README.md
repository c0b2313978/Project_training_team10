# MazeRPG – Map/JSON 仕様 & 実行手順

本プロジェクトは **grid（地形）をテキスト**, **オブジェクト/ギミック等は JSON** に分離した構成です。  
実装は dataclass を使わず、パーサは人間が正しく書く前提で最小限です。

---

## ディレクトリ構成（例）

```

project/
main.py               # 実行スクリプト（本READMEにある実装骨子）
maps/
map01.txt
map01.json
map02.txt
map02.json
map06.txt
map06.json

````

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
{"id":"K1","type":"key","pos":[2,6],"hidden":false,"params":{"key_id":"gold"}}
{"id":"TR1","type":"trap","pos":[3,4],"hidden":false,"params":{"dmg":10,"once":1}}
```

* `weapon`: 取得即 `ATK += atk`
* `potion`: インベントリに入る。`u` で使用→HP全快
* `key`: `params.key_id` をプレイヤーが所持
* `trap`: 踏むと `dmg` ダメージ。`once=1` なら一度きり。

### monsters

```json
{"id":"M1","pos":[2,8],"ai":"static","move":0,"drop":["P1"]}
{"id":"M2","pos":[6,4],"ai":"random","params":{"p":0.5},"move":1,"drop":["gen:weapon:+3"]}
{"id":"M3","pos":[8,6],"ai":"chase","params":{"range":6},"move":1}
{"id":"M4","pos":[10,11],"ai":"patrol","params":{"path":[[10,11],[10,15],[8,15],[8,11]]},"move":2}
```

* `ai`: `static` / `random` / `chase` / `patrol`
* `move`: 何ターンごとに移動するか（0=動かない）
* `params`:

  * `random`: `{ "p": 0.5 }` 移動確率
  * `chase`: `{ "range": 6 }` 追跡開始距離
  * `patrol`: `{ "path": [[r,c], ...] }` 巡回点
* `drop`: 撃破時ドロップ。`"gen:weapon:+3"`, `"gen:potion"`, `"gen:key:red"` または既存 item の `"ID"`

> HP/ATK は**フロア入場時に自動設定**前提（実装側で難易度係数をかける等）。サンプル実装では未指定時に簡易値 `(hp=30, atk=6)` を補完。

### doors

```json
{"id":"Dgold","pos":[10,15],"key":"gold","locked":true}
```

* 同セルに入ると自動で解錠を試みる（鍵条件を満たす場合のみ）。

### chests

```json
{"id":"C1","pos":[5,6],"key":"red","opened":false,"contents":["gen:weapon:+7","P1"]}
```

* 同セルに入ると自動で開封を試みる。中身はセル上にスポーン。

### teleports

```json
{"id":"T1","src":[7,12],"dst":[3,2],"bi":true}
```

* 停止時に起動（双方向は `bi: true`）。

### gimmicks

```json
{
  "ice": [[1,2],[1,3],[1,4]],     // 氷セル（直進）
  "hp_drain": 1,                   // 1セルごとにHP減（滑走中も）
  "monster_ice": true,             // モンスターが氷に入れるか
  "trap_cells": [[3,1]]            // 地形罠（固定10ダメ）
}
```

---

## ゲームループと操作

* `run([...])` に `[(map_txt, None), ...]` を渡すと順にプレイします
* 5フロアクリアでゲームクリア（`GameState.go_next_floor()` 内で判定）
* コマンド: **w/a/s/d** 移動, **u** ポーション使用, **q** 終了
* 描画優先: **プレイヤー > モンスター > ドア(閉) > チェスト(未開) > 隠しアイテム(?) > ゴール > テレポ > 床**
  隠しアイテムは `reveal_hidden=true` のとき `?` で表示（踏むと正体判明/取得）

---

## 実装ポリシー（本リポの方針）

* **パーサは簡素**：マップ/JSONは正しく書かれている前提。過度な防御的コードは省略。
* **責務の集約**：描画・移動・戦闘・敵AI・ドロップ・扉/宝箱・判定は **`GameState` メソッド** に集約。
  外側からは `render()` と `step_turn(cmd)` を呼ぶだけで進行可能。
* **拡張しやすさ**：

  * AIの追加：`monsters_act()` の分岐に追加
  * 新アイテム：`on_step_common()` で type 分岐を追加
  * 追加ギミック：`on_step_common()` / `_passable_*()` / `_compute_slide_path()` にフック

---

## よくある拡張

* **難易度スケーリング**：`__init__` で `for m in fl.monsters.values(): m['hp']=..., m['atk']=...` をフロア番号で係数化
* **セーブ/ロード**：`GameState` の `floor_idx / cleared_count / player状態 / 各フロアの items/doors/chests/monsters` を JSON dump/load
* **UI差し替え**：`render()` と `read_cmd()` を置き換えても、`step_turn()` はそのまま使える

---

## 動作確認

```python
# main.py
from main import run
run([
  ("maps/map06.txt", None),
  # ("maps/map07.txt", None),
])
```

* 期待値：氷上で直進、1歩ごとHP-1、`?` 表示のセルに乗るとアイテム判明、モンスターはAIに応じて行動、ゴール到達+鍵条件でクリア。

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

## トラブルシュート

* **「gridは#/ .のみ」エラー**
  → grid行に余計な文字が混入していないか確認（全角や空白末尾に注意）
* **JSONの `start`/`goal.reach` などは配列**
  → `(r,c)` ではなく `[r,c]` で書く（パース簡略化のため）
* **隠しアイテムが見えない**
  → `reveal_hidden` が `true` か、`hidden: true` の座標が正しいか確認