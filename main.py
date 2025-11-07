# Team 10
import os

from modules.game_state import GameState
from modules.constants import TEXT_DIR_PATH, sample_map_data

# Main ループ
def main():
    game_state = GameState()
    while game_state.game_state():
        game_state.step_turn()

def tmp():
    game_state = GameState(requires_map_file_path=["map_data/map05.txt", "map_data/map05.txt"])  # デバッグ用：特定フロア指定
    while game_state.game_state():
        # command = game_state.read_command()
        # os.system('cls' if os.name == 'nt' else 'clear')  # 画面クリア
        game_state.step_turn()


if __name__ == "__main__":
    main()
    #tmp()