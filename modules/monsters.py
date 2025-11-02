# ==================== モンスタークラス ====================
class Monster:
    def __init__(self, id, pos, ai_type, ai_params = {}, move_every=1, drop_list=[]):
        self.id = id  # 一意なID
        self.pos = tuple(pos)  # (row, col)

        self.ai_type = ai_type  # 'static'|'random'|'chase'|'patrol'
        self.ai_params = ai_params  # AIの行動についての追加パラメータ辞書

        self.move_every = move_every  # 何ターンごとに移動するか（0=動かない）
        self.turn_counter = 0  # ターンカウンター
        self.drop_list = drop_list  # 撃破時ドロップアイテムIDリスト
        
        # ステータスはフロア侵入時に自動で設定（要件）
        self.alive = True  # 生存フラグ
        self.hp = 0
        self.attack = 0
    
    def __repr__(self):
        return f"Monster(id={self.id}, pos={self.pos}, ai_type={self.ai_type}, ai_params={self.ai_params}, move_every={self.move_every}, drop_list={self.drop_list})"
    
    def init_status(self, player_hp, player_attack):
        """ プレイヤーステータスに基づき、モンスターのステータスを初期化する """  # TODO: ステータス設定 要調整
        self.hp = player_hp
        self.attack = player_attack

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