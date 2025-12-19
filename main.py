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
            info, legal_actions = game_state.get_known_info()
            command = agent.decide_move(info, legal_actions)
            input()  # 一時停止（手動操作時用）
        game_state.step_turn(command)


full_maps = [f"map_data/map{file_name:02d}.txt" for file_name in range(1, 9)]
easy_maps = [f"map_data/map{file_name:02d}.txt" for file_name in (1, 2, 3, 5, 6)]

def tmp(auto_play=False):
    # game_state = GameState(requires_map_file_path=easy_maps)  # デバッグ用：特定フロア指定
    game_state = GameState(requires_map_file_path=["map_data/map08.txt"])  # デバッグ用：特定フロア指定
    agent = ModeBasedAI(game_state = game_state)
    
    while game_state.game_state():
        command = ""
        if auto_play:
            info, legal_actions = game_state.get_known_info()
            command = agent.decide_move(info, legal_actions)
            input()  # 一時停止（手動操作時用）
        game_state.step_turn(command)


def performance_evaluation(times = 100, agent_class = ModeBasedAI):
    from random import seed
    seed(1)  # 再現性のため乱数シード固定

    win_count = 0
    for i in range(times):
        print(f"=== 試行回数: {i+1} / {times} ===")
        output_file_path = f"logs/attempt_{i+1:03d}.txt"
        output_file_object = open(output_file_path, mode='w', encoding='utf-8')
        game_state = GameState(output_file_object=output_file_object)
        agent = agent_class(game_state = game_state, output_file_object=output_file_object)
        
        try:
            while game_state.game_state():
                info, legal_actions = game_state.get_known_info()
                command = agent.decide_move(info, legal_actions)
                game_state.step_turn(command)
            
            if game_state.is_game_cleared:
                win_count += 1
            print(f"現在の勝率: {win_count / (i+1) * 100:.2f}%\n")
        finally:
            output_file_object.close()

    print(f"=== 最終結果 勝ち: {win_count}． 勝率: {win_count / times * 100:.2f}% ===")


if __name__ == "__main__":
    # main(auto_play=True)
    # tmp(auto_play=False)
    # tmp(auto_play=True)
    performance_evaluation(times=100, agent_class=ModeBasedAI)
