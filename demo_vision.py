#!/usr/bin/env python3
"""Demo to show vision restriction in action"""

from modules.floor import Floor
from modules.player import Player

def demo_range_vision():
    print("=" * 70)
    print("DEMO: Range-based Vision (k=3 squares)")
    print("=" * 70)
    print("\nThis demo shows how the player's vision updates as they move.")
    print("Only cells within 3 squares are visible.\n")
    
    floor = Floor("map_data/test_vision_range.txt", floor_id="demo")
    player = Player(floor.start)
    
    path = [
        (4, 4, "Starting position"),
        (4, 7, "Moved 3 steps right"),
        (4, 10, "Moved 6 steps right"),
        (4, 12, "Reached goal!"),
    ]
    
    for pos_r, pos_c, desc in path:
        player.position = (pos_r, pos_c)
        print(f"{desc}: {player.position}")
        print("-" * 70)
        floor.print_grid(player, full_width=True)
        print()

def demo_los_vision():
    print("=" * 70)
    print("DEMO: Line-of-Sight Vision")
    print("=" * 70)
    print("\nThis demo shows how walls block the player's line of sight.")
    print("The player can see until their vision hits a wall.\n")
    
    floor = Floor("map_data/test_vision_los.txt", floor_id="demo")
    player = Player(floor.start)
    
    path = [
        (4, 4, "Starting position - walls block vision"),
        (4, 7, "Moved right - different view"),
        (1, 7, "Moved to open area - wider vision"),
    ]
    
    for pos_r, pos_c, desc in path:
        player.position = (pos_r, pos_c)
        print(f"{desc}: {player.position}")
        print("-" * 70)
        floor.print_grid(player, full_width=True)
        print()

if __name__ == "__main__":
    demo_range_vision()
    demo_los_vision()
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)
