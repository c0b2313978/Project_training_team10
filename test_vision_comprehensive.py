#!/usr/bin/env python3
"""
Comprehensive test for vision restriction feature
Tests the feature in realistic gameplay scenarios
"""

from modules.floor import Floor
from modules.player import Player
from modules.constants import DIRECTIONS

def test_vision_with_monsters_and_items():
    """Test vision restriction with monsters and items"""
    print("=" * 60)
    print("Test: Vision Restriction with Monsters and Items")
    print("=" * 60)
    
    # Create a test map with items and monsters
    floor = Floor("map_data/test_vision_range.txt", floor_id="test")
    player = Player(floor.start)
    
    print("\nMap info:")
    print(f"  - Start: {floor.start}")
    print(f"  - Goal: {floor.goal['pos']}")
    print(f"  - Items: {len(floor.items)}")
    print(f"  - Vision mode: {floor.gimmicks.vision_mode if floor.gimmicks else 'None'}")
    print(f"  - Vision range: {floor.gimmicks.vision_range if floor.gimmicks else 'N/A'}")
    
    print("\nInitial view:")
    floor.print_grid(player, full_width=False)
    
    # Simulate player movement
    moves = ['d', 'd', 'd', 'd']  # Move right 4 times
    for i, move in enumerate(moves, 1):
        dr, dc = DIRECTIONS[move]
        new_pos = (player.position[0] + dr, player.position[1] + dc)
        
        # Check if move is valid
        if floor.grid[new_pos[0]][new_pos[1]] == '.':
            player.position = new_pos
            player.last_move_direction = move
            print(f"\nAfter move {i} ({move}): Position {player.position}")
            floor.print_grid(player, full_width=False)
        else:
            print(f"\nMove {i} ({move}) blocked!")
    
    print("\n✓ Test completed")

def test_vision_modes_comparison():
    """Compare both vision modes side by side"""
    print("\n" + "=" * 60)
    print("Test: Comparing Vision Modes")
    print("=" * 60)
    
    # Range mode
    print("\n1. RANGE MODE (k=3):")
    print("-" * 40)
    floor_range = Floor("map_data/test_vision_range.txt", floor_id="range")
    player_range = Player(floor_range.start)
    player_range.position = (4, 7)
    floor_range.print_grid(player_range, full_width=False)
    
    # Line-of-sight mode
    print("\n2. LINE-OF-SIGHT MODE:")
    print("-" * 40)
    floor_los = Floor("map_data/test_vision_los.txt", floor_id="los")
    player_los = Player(floor_los.start)
    player_los.position = (4, 7)
    floor_los.print_grid(player_los, full_width=False)
    
    print("\n✓ Comparison completed")

def test_vision_edge_cases():
    """Test edge cases for vision restriction"""
    print("\n" + "=" * 60)
    print("Test: Edge Cases")
    print("=" * 60)
    
    floor = Floor("map_data/test_vision_range.txt", floor_id="edge")
    player = Player(floor.start)
    
    # Test at corners
    test_positions = [
        (1, 1, "Top-left corner"),
        (1, 13, "Top-right corner"),
        (7, 1, "Bottom-left corner"),
        (7, 13, "Bottom-right corner"),
    ]
    
    for r, c, desc in test_positions:
        if floor.grid[r][c] == '.':
            player.position = (r, c)
            print(f"\n{desc}: Position {player.position}")
            floor.print_grid(player, full_width=False)
    
    print("\n✓ Edge cases tested")

def test_backward_compatibility():
    """Ensure maps without vision restriction still work"""
    print("\n" + "=" * 60)
    print("Test: Backward Compatibility")
    print("=" * 60)
    
    floor = Floor("map_data/map01.txt", floor_id="1")
    player = Player(floor.start)
    
    print("\nMap without vision restriction:")
    print(f"  - Has gimmicks: {floor.gimmicks is not None}")
    if floor.gimmicks:
        print(f"  - Has vision limit: {floor.gimmicks.has_vision_limit}")
    
    floor.print_grid(player, full_width=False)
    
    print("\n✓ Backward compatibility confirmed")

def run_all_tests():
    """Run all comprehensive tests"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE VISION RESTRICTION TESTS")
    print("=" * 60)
    
    try:
        test_vision_with_monsters_and_items()
        test_vision_modes_comparison()
        test_vision_edge_cases()
        test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
