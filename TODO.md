# TODOチェックリスト

## ゲーム進行・UX
- [ ] GameState.__init__ で利用可能なフロア一覧から `random.sample` で TARGET_CLEAR 分を抽出し、デバッグ指定時もグローバルを書き換えずインスタンス側でクリア目標数を持つ（modules/game_state.py:13）。
- [ ] 各フロア開始時にシンボル凡例と操作キーのヘルプを `print_grid` もしくは専用関数で表示する。
- [ ] ターン処理の主要イベント（移動、戦闘、アイテム取得）を `logging` モジュールでファイル出力できるようにする（modules/game_state.py:58）。

## プレイヤーとアイテム
- [x] コマンド `u` でポーション消費・HP回復（modules/player.py:36）。
- [ ] `Item` の武器パラメータをマップ定義のキー（例: `atk`, `attack`）から解釈し、攻撃力上昇を動的に適用する（modules/items.py:36）。
- [ ] プレイヤーに `keys` セット（または Counter）を追加し、鍵アイテムの取得・消費を専用メソッドで管理する（modules/player.py:22）。
- [ ] 隠しアイテム踏破時に `reveal_hidden` が false でも `picked=True` にして可視化する。併せて、床タイルを再描画する（modules/floor.py:275）。
- [ ] アイテム取得時に種別ごとのメッセージや効果概要を表示し、凡例と合わせてユーザー体験を改善する。

## モンスターと戦闘
- [ ] `Monster.init_status` をプレイヤー状態・フロア難度・ai_params を基にHP/攻撃力へ反映させる（modules/monsters.py:31）。
- [ ] AIごとの ai_params を反映する：`random` で移動確率 p、`chase` で射程 range、`patrol` で `path`（または points）リストを正しく使用する（modules/monsters.py:38, modules/monsters.py:65）。
- [ ] ドロップリストの `gen:` トークンをパースし、武器/ポーションなどを動的生成してプレイヤー／フロアに配置する（modules/floor.py:309）。

## 環境ギミック
- [ ] ドア進入時に必要鍵を照合し、成功時に `Door.opened` とマップ上の通行セルを更新する（modules/objects.py:6, modules/floor.py:268）。
- [ ] チェスト開封で鍵チェック、`contents` に既存ID/`gen:` 両対応する処理を実装する（modules/objects.py:15, modules/floor.py:268）。
- [ ] テレポート踏破時に `Teleport.target` へ座標を移し、双方向設定も考慮する（modules/objects.py:27）。
- [ ] `gimmicks` セクションを読み込んで氷滑走・HP減少・地形罠フラグを適用する（modules/objects.py:33, modules/floor.py:49）。
- [ ] タイル状態が変化した際に `movable_cells` 等の通行情報を更新する（modules/floor.py:21）。

## ドキュメント・デバッグ
- [ ] README に操作入力、マップシンボル凡例、既知の制限事項、ログ出力方法を追記する（README.md）。
- [ ] デバッグ用のサンプル入力／ゲームログを `docs/` などに整理する。
- [ ] map_data 配下の定義とコードの想定キー（例: atk, path）を表形式でまとめ、実装とのズレを検出しやすくする。

## AI制御対応
- [ ] GameState.step_turn で渡された command を尊重し、未指定時のみ入力を読むようにして外部AIからの行動注入を可能にする（modules/game_state.py:83-105）。
- [ ] プレイヤー行動を (action, payload) 形式で扱える Command データ構造を用意し、ポーションIDなどの追加入力を command 経由で受けられるよう統一する（modules/game_state.py:74-101）。
- [ ] Floor.enter_cell / battle_monster が print ではなくイベントリストを返し、GameState.step_turn がターン結果を返却できるようリファクタリングする（modules/game_state.py:83-141, modules/floor.py:268-322）。
- [ ] RNG のシード設定や乱数源の注入ポイントを GameState / Monster に追加し、自動プレイ検証で再現性を確保する（modules/game_state.py:15-18, modules/monsters.py:42-63）。