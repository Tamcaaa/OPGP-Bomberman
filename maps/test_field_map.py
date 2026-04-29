# 0 - Ground, 1 - Unbreakable wall, 2 - Breakable wall, 3 - Menu Bar
# 4 - Cave blue, 5 - Cave blue, 8- Sewer
from maps.map_generator import generate_map

MAP_NAMES = ["Classic", "Crystal Caves", "Urban Assault", "Ancient Ruins", "Desert Maze"]

def get_map(map_name: str):
    return generate_map(map_name)