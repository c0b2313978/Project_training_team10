#!/usr/bin/env python3
"""Interactive test to play with vision restriction"""

from modules.game_state import GameState

def test_interactive():
    """Test vision restriction interactively"""
    print("Testing Vision Restriction with map test_vision_range")
    print("Commands: w/a/s/d to move, q to quit")
    print("=" * 50)
    
    game_state = GameState(requires_map_file_path=["map_data/test_vision_range.txt"])
    
    # Skip the opening
    
    for i in range(10):  # Max 10 moves
        if not game_state.game_state():
            break
        
        # Auto move right
        game_state.step_turn(command='d')
        
        if game_state.player.position[1] >= 12:  # Reached goal column
            break
    
    if game_state.is_game_cleared:
        print("\n✓ Game cleared successfully!")
    elif game_state.is_game_over:
        print("\n✗ Game over!")
    else:
        print(f"\n- Player position: {game_state.player.position}")

def test_los():
    """Test line-of-sight vision"""
    print("\n" + "=" * 50)
    print("Testing Line-of-Sight Vision")
    print("=" * 50)
    
    game_state = GameState(requires_map_file_path=["map_data/test_vision_los.txt"])
    
    for i in range(10):
        if not game_state.game_state():
            break
        
        # Auto move right
        game_state.step_turn(command='d')
        
        if game_state.player.position[1] >= 12:
            break
    
    if game_state.is_game_cleared:
        print("\n✓ Game cleared successfully!")
    elif game_state.is_game_over:
        print("\n✗ Game over!")
    else:
        print(f"\n- Player position: {game_state.player.position}")

if __name__ == "__main__":
    test_interactive()
    test_los()
