# Team 10
import os

from modules.game_state import GameState
from modules.constants import TEXT_DIR_PATH, sample_map_data
from modules.self_made_AI import RandomAI

# Main ループ
def main(auto_play=False):
    game_state = GameState()
    agent = RandomAI() if auto_play else None
    while game_state.game_state():
        command = ""
        if auto_play:
            command = agent.decide_move(game_state)
        game_state.step_turn(command)

def tmp(auto_play=False):
    game_state = GameState(requires_map_file_path=["map_data/map01.txt"])  # デバッグ用：特定フロア指定
    # game_state = GameState()
    agent = RandomAI() if auto_play else None
    while game_state.game_state():
        command = ""
        if auto_play:
            command = agent.decide_move(game_state)
        game_state.step_turn(command)


if __name__ == "__main__":
    main(auto_play=True)
    # tmp(auto_play=True)
