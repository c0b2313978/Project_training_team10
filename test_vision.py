#!/usr/bin/env python3
"""Test script for vision restriction gimmick"""

from modules.floor import Floor
from modules.player import Player

def test_vision_range():
    """Test range-based vision restriction"""
    print("=" * 50)
    print("Testing Range-based Vision (3 squares)")
    print("=" * 50)
    
    floor = Floor("map_data/test_vision_range.txt", floor_id="test_range")
    player = Player(floor.start)
    
    print("\nInitial position:")
    floor.print_grid(player, full_width=False)
    
    print("\nVision gimmick enabled:", floor.gimmicks.has_vision_limit if floor.gimmicks else False)
    if floor.gimmicks and floor.gimmicks.has_vision_limit:
        print(f"Vision mode: {floor.gimmicks.vision_mode}")
        print(f"Vision range: {floor.gimmicks.vision_range}")
    
    # Move player to test vision update
    player.position = (4, 7)
    player.last_move_direction = 'd'
    print("\nAfter moving to (4, 7):")
    floor.print_grid(player, full_width=False)

def test_vision_line_of_sight():
    """Test line-of-sight vision restriction"""
    print("\n" + "=" * 50)
    print("Testing Line-of-Sight Vision")
    print("=" * 50)
    
    floor = Floor("map_data/test_vision_los.txt", floor_id="test_los")
    player = Player(floor.start)
    
    print("\nInitial position:")
    floor.print_grid(player, full_width=False)
    
    print("\nVision gimmick enabled:", floor.gimmicks.has_vision_limit if floor.gimmicks else False)
    if floor.gimmicks and floor.gimmicks.has_vision_limit:
        print(f"Vision mode: {floor.gimmicks.vision_mode}")
    
    # Move player to test vision update
    player.position = (4, 7)
    player.last_move_direction = 'd'
    print("\nAfter moving to (4, 7):")
    floor.print_grid(player, full_width=False)

def test_no_vision_restriction():
    """Test that maps without vision restriction still work"""
    print("\n" + "=" * 50)
    print("Testing Normal Map (No Vision Restriction)")
    print("=" * 50)
    
    floor = Floor("map_data/map01.txt", floor_id="1")
    player = Player(floor.start)
    
    print("\nInitial position:")
    floor.print_grid(player, full_width=False)
    
    print("\nVision gimmick enabled:", floor.gimmicks.has_vision_limit if floor.gimmicks else False)

if __name__ == "__main__":
    test_vision_range()
    test_vision_line_of_sight()
    test_no_vision_restriction()
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
