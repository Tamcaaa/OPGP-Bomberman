import random
import config

# Konštanty
rows = config.ROWS
cols = config.COLS

# Tile hodnoty
menu    = config.MENU
ground  = config.GROUND
wall    = config.WALL
brick   = config.BRICK
portal_blue  = config.PORTAL_BLUE
portal_red   = config.PORTAL_RED
sewer   = config.SEWER
brick_density = config.BRICK_DENSITY

corner_safe = {
    "spawn1": [(r, c) for r in range(1, 4) for c in range(0, 3)],       # ľavý horný
    "spawn2": [(r, c) for r in range(1, 4) for c in range(29, 32)],     # pravý horný
    "spawn3": [(r, c) for r in range(15, 18) for c in range(0, 3)],     # ľavý dolný
    "spawn4": [(r, c) for r in range(15, 18) for c in range(29, 32)],   # pravý dolný
}
all_safe = set()
for cells in corner_safe.values():
    all_safe.update(cells)


def is_fixed_wall(row, col):
    """Každý sudý riadok (okrem row 0) a každý sudý stĺpec tvorí pevnú mriežku."""
    # row 0 = menu bar – preskočíme
    if row == 0:
        return False
    return (row % 2 == 0) and (col % 2 == 0)


def generate_map(map_name: str, seed: int | None = None) -> list[list[int]]:
    if seed is not None:
        random.seed(seed)

    specials = config.MAP_FIXED_SPECIALS.get(map_name, {"portals_blue": [], "portals_red": [], "sewers": 0})
    
    special_positions = {}
    for pos in specials["portals_blue"]:
        special_positions[pos] = portal_blue
    for pos in specials["portals_red"]:
        special_positions[pos] = portal_red

    grid = []

    # Najprv vygeneruj grid bez sewers
    for r in range(rows):
        row = []
        for c in range(cols):
            pos = (r, c)
            if r == 0:
                row.append(menu)
            elif pos in special_positions:
                row.append(special_positions[pos])
            elif is_fixed_wall(r, c):
                row.append(wall)
            elif pos in all_safe:
                row.append(ground)
            else:
                row.append(brick if random.random() < brick_density else ground)
        grid.append(row)

    # Náhodne umiestni sewers na voľné políčka (nie rohy, nie walls)
    num_sewers = specials.get("sewers", 0)
    if num_sewers > 0:
        candidates = []
        for r in range(1, rows):
            for c in range(cols):
                pos = (r, c)
                if pos in all_safe:
                    continue
                if pos in special_positions:
                    continue
                if is_fixed_wall(r, c):
                    continue
                candidates.append((r, c))
        
        chosen = random.sample(candidates, min(num_sewers, len(candidates)))
        for r, c in chosen:
            grid[r][c] = sewer

    return grid


def print_map(grid: list[list[int]]):
    print("[")
    for row in grid:
        print(f"    {row},")
    print("]")


def generate_all_maps(seed: int | None = None) -> dict[str, list[list[int]]]:
    maps = {}
    for name in config.MAP_FIXED_SPECIALS:
        maps[name] = generate_map(name, seed)
    return maps


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None

    all_maps = generate_all_maps(seed)
    for name, grid in all_maps.items():
        print(f"\n# ── {name} ──")
        print_map(grid)