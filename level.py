import pygame
import config

filename = "levels/level1.txt"


def load_level(filename):
    try:
        level = []
        with open(filename, 'r') as f:
            lines = f.readlines()

            for line in lines:
                row = [int(cell) for cell in line.strip()]
                level.append(row)
        return level
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        raise


#Funkcia na vykreslenie levelu
def draw_level(screen, level):
    for row_idx, row in enumerate(level):
        for col_idx, tile in enumerate(row):
            x = col_idx * config.GRID_SIZE
            y = row_idx * config.GRID_SIZE

            # Vykreslenie podľa hodnoty tile
            if tile == 1:  # Stena
                pygame.draw.rect(screen, (0, 0, 255), (x, y, config.GRID_SIZE, config.GRID_SIZE))  # Blue
            elif tile == 0:  # Prázdny priestor
                pygame.draw.rect(screen, (255, 255, 255), (x, y, config.GRID_SIZE, config.GRID_SIZE))  # White
            elif tile == 2:  # Špeciálny objekt (napr. power-up)
                pygame.draw.rect(screen, (0, 255, 0), (x, y, config.GRID_SIZE, config.GRID_SIZE))  # Green