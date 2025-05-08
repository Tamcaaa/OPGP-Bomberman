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

MUSIC_VOLUME = {
    "main_menu_volume": 0.25,
    "level_volume": 0.5,
    "game_over_volume": 0.5,
    "explosion_volume": 1,
    "walk_volume": 0.5,
    "death_volume": 1

}

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 128, 0)
COLOR_DARK_GREEN = (80, 160, 0)
COLOR_LIGHT_GREEN = (144, 208, 80)
COLOR_LIGHT_BLUE = (70, 130, 180)
BACKGROUND_COLOR = (162, 235, 154)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)

# ----------------------------------------------------------------Main_menu-----------------------------------------------------------------

# ----------------------------------------------------------------Test_field----------------------------------------------------------------
PLAYER_IFRAMES = 0.75
MAX_QUEUE = 3
SPAWN_POINTS = {"spawn1": (0, 30),
                "spawn2": (930, 30),
                "spawn3": (0, 510),
                "spawn4": (930, 510)}
# Movement keys
PLAYER1_MOVE_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE]
PLAYER2_MOVE_KEYS = [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_KP0]
# Player images
PLAYER1_IMAGES = {
    "down": pygame.image.load("assets/player_color/p_1_down.png"),
    "up": pygame.image.load("assets/player_color/p_1_up.png"),
    "left": pygame.image.load("assets/player_color/p_1_left.png"),
    "right": pygame.image.load("assets/player_color/p_1_right.png")
}
PLAYER2_IMAGES = {
    "down": pygame.image.load("assets/player_color/p_2_down.png"),
    "up": pygame.image.load("assets/player_color/p_2_up.png"),
    "left": pygame.image.load("assets/player_color/p_2_left.png"),
    "right": pygame.image.load("assets/player_color/p_2_right.png")
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
# -----------------------------------------------------------------Power_up-----------------------------------------------------------------

POWERUP_TYPES = [
    "bomb_powerup",  # Increases max bombs
    "range_powerup",  # Increases explosion range
    "freeze_powerup",  # Freezes the other player
    "live+_powerup",  # Adds an extra life
    "shield_powerup"]  # Temporary invincibility
POWERUP_SPAWNING_RATE = 0.4
POWERUP_DURATIONS = {
    'shield_powerup': 15,
    'freeze_powerup': 5,
}
