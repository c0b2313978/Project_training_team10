# Team 10
import json
import random
import time

from modules.game_state import GameState




# # Main ループ
# def main():
#     print_game_text(TEXT_DIR_PATH+"Firstgame_ui.txt")
#     time.sleep(1)
#     print_game_text(TEXT_DIR_PATH+"Basic_rule.txt")
#     time.sleep(1)
#     print_game_text(TEXT_DIR_PATH+"Opening.txt")
#     time.sleep(1)


def tmp():
    game_state = GameState()
    while game_state.game_state():
        # command = game_state.read_command()
        game_state.step_turn()


if __name__ == "__main__":
    # main()
    tmp()