## TODO（ゲーム進行）
- 5層選定と進行管理: GameState と random_select_map が繋がっておらず、5層を順番に遊ぶ仕組みがない（main.py:37, main.py:401）。
- フロア遷移とクリア判定: tmp_run_game が単一マップ固定で、ゴール到達時に cleared_count や TARGET_CLEAR を使った判定が行われていない（main.py:7, main.py:504）。
- ゴール条件の拡張: goal.type が reach のみ想定で、keys_only / reach_and_keys / multiple を判定していない（main.py:111, main.py:525）。
- ゲームオーバー処理: HP0判定と is_game_over フラグ更新が存在せず、敗北時の遷移が未実装（main.py:37, main.py:392）。

## TODO（プレイヤー・アイテム）
- アイテム効果適用: Key/Weapon/Potion/Trap.apply_effect が未実装で、攻撃力上昇やダメージ、鍵取得が反映されない（main.py:265, main.py:274, main.py:282, main.py:289）。
- ポーション使用コマンド: u が入力チェックのみで、インベントリからの消費やHP回復を行っていない（main.py:474）。
- 鍵・インベントリ管理: Player に鍵保管やアイテムスタック処理がなく、ドアや宝箱と連動できない（main.py:388）。
- 罠ダメージ: 罠アイテムに踏んだタイミングでHPを減らす処理が存在しない（main.py:289）。
- 隠しアイテム発見: reveal_hidden の表示はあるが、踏んだ際に正体を公開して picked を更新する仕組みがない（main.py:192）。

## TODO（モンスター・戦闘）
- 戦闘解決: プレイヤーがモンスターと同じマスに入っても戦闘が発生せず、ターン制バトルやHP減算が未実装（main.py:202, main.py:519）。
- 能力値初期化: Monster.init_status が仮実装のままで、難易度係数や個体値が設定されない（main.py:360）。
- AI挙動: ai_type ごとの行動（random/chase/patrol）や move_every が処理されず、全モンスターが実質不動（main.py:345）。
- ドロップ生成: 撃破後に drop_list を参照してアイテムを生成する処理が未実装（main.py:348）。

## TODO（ギミック・環境）
- ドア解錠: Door を通過可能かチェックするロジックがなく、キー判定も未実装（main.py:307, main.py:485）。
- 宝箱開封: Chest の鍵チェックと contents のスポーン処理が存在しない（main.py:317）。
- テレポート: タイル踏破時に Teleport で移動する仕組みがない（main.py:328）。
- ギミック初期化: Floor の gimmicks が未読込・未適用で、滑走やHP減少などの効果を管理できていない（main.py:101, main.py:378）。
- 通行状態更新: 「一度通った道が使えなくなる」等に対応するセル状態更新がなく、movable_cells も固定のまま（main.py:62）。