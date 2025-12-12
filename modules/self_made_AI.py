import random
from modules.floor import Floor
from modules.game_state import GameState
from modules.player import Player


class RandomAI:
    def __init__(self, name="RandomAI"):
        self.name = name

    def decide_move(self, game_state: GameState):
        actions = game_state.get_legal_actions()
        return random.choice(actions)
