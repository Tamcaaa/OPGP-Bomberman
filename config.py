import pygame

# CONSTANTS
SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FONT_SIZE = 24
H1_SIZE = 54
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 30
BUTTON_RADIUS = 4
GRID_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
MOVE_COOLDOWN = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)
# ------------------------------------------------------------------------------------------------------------------------------------------
# Test_Field
PLAYER_IFRAMES = 0.75
MAX_QUEUE = 3
SPAWN_POINTS = {"spawn1": (0, 0),
                "spawn2": (930, 0),
                "spawn3": (0, 510),
                "spawn4": (930, 510)}
# Movement keys
PLAYER1_MOVE_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE]
PLAYER2_MOVE_KEYS = [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_KP0]

# Player images
PLAYER1_IMAGES = {
    "down": pygame.image.load("photos/player_color/p_1_down.png"),
    "up": pygame.image.load("photos/player_color/p_1_up.png"),
    "left": pygame.image.load("photos/player_color/p_1_left.png"),
    "right": pygame.image.load("photos/player_color/p_1_right.png")
}
PLAYER2_IMAGES = {
    "down": pygame.image.load("photos/player_color/p_2_down.png"),
    "up": pygame.image.load("photos/player_color/p_2_up.png"),
    "left": pygame.image.load("photos/player_color/p_2_left.png"),
    "right": pygame.image.load("photos/player_color/p_2_right.png")
}

PLAYER_CONFIG = {
    1: {
        'move_keys': PLAYER1_MOVE_KEYS,
        'images': PLAYER1_IMAGES,
    },
    2: {
        'move_keys': PLAYER2_MOVE_KEYS,
        'images': PLAYER2_IMAGES,
    }
}
