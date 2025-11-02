# Team 10
import json
import random
import time

from modules.game_state import GameState
from modules.constants import TEXT_DIR_PATH, sample_map_data

# # Main ループ
# def main():
#     print_game_text(TEXT_DIR_PATH+"Firstgame_ui.txt")
#     time.sleep(1)
#     print_game_text(TEXT_DIR_PATH+"Basic_rule.txt")
#     time.sleep(1)
#     print_game_text(TEXT_DIR_PATH+"Opening.txt")
#     time.sleep(1)

def tmp():
    game_state = GameState(requires_map_file_path=["map_data/sample01.txt", "map_data/sample06.txt"])  # デバッグ用：特定フロア指定
    # game_state = GameState(requires_map_file_path=sample_map_data)  # デバッグ用：特定フロア指定
    while game_state.game_state():
        # command = game_state.read_command()
        game_state.step_turn()


if __name__ == "__main__":
    # main()
    tmp()