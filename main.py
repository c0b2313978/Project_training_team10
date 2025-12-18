# Team 10
import os

from modules.game_state import GameState
from modules.constants import TEXT_DIR_PATH, sample_map_data
from modules.self_made_AI import RandomAI, ModeBasedAI

# Main ループ
def main(auto_play=False):
    game_state = GameState()
    agent = ModeBasedAI()
    
    while game_state.game_state():
        command = ""
        if auto_play:
            command = agent.decide_move(game_state)
        input()  # 一時停止（手動操作時用）
        game_state.step_turn(command)


full_maps = [f"map_data/map{file_name:02d}.txt" for file_name in range(1, 9)]

def tmp(auto_play=False):
    # game_state = GameState(requires_map_file_path=full_maps)  # デバッグ用：特定フロア指定
    game_state = GameState(requires_map_file_path=["map_data/map06.txt"])  # デバッグ用：特定フロア指定
    agent = ModeBasedAI(game_state = game_state)
    
    while game_state.game_state():
        command = ""
        if auto_play:
            command = agent.decide_move(game_state)
        input()  # 一時停止（手動操作時用）
        game_state.step_turn(command)


if __name__ == "__main__":
    # main(auto_play=True)
    tmp(auto_play=True)
