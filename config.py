import pygame

# CONSTANTS
SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FONT_SIZE = 30
H1_SIZE = 54
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 30
BUTTON_RADIUS = 4
GRID_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
MOVE_COOLDOWN = 120


MUSIC_VOLUME = {
    "main_menu_volume": 0.25,
    "level_volume": 0.4,
    "game_over_volume": 0.5,
    "explosion_volume": 0.5,
    "walk_volume": 0.1,
    "death_volume": 1

}

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 41, 0)
COLOR_BEIGE = (211, 161, 105)
COLOR_GREEN = (0, 128, 0)
COLOR_DARK_GREEN = (80, 160, 0)
COLOR_LIGHT_GREEN = (144, 208, 80)
COLOR_BLUE = (0, 68, 255)
COLOR_LIGHT_BLUE = (70, 130, 180)
BACKGROUND_COLOR = (162, 235, 154)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (95, 68, 46)
# ----------------------------------------------------------------Player_colors-------------------------------------------------------------
WHITE_PLAYER  = (255, 255, 255)   
BLACK_PLAYER  = (103, 103, 103)    
RED_PLAYER    = (220, 50, 50)    
BLUE_PLAYER   = (50, 100, 220)   
DARK_GREEN_PLAYER  = (30, 160, 80) 
LIGHT_GREEN_PLAYER = (100, 220, 100) 
YELLOW_PLAYER = (255, 230, 100)  
PINK_PLAYER   = (255, 120, 180)   
ORANGE_PLAYER = (255, 165, 50)   
PURPLE_PLAYER = (150, 100, 255)  
BROWN_PLAYER  = (160, 120, 80)  
CYAN_PLAYER   = (50, 220, 220) 


# ----------------------------------------------------------------Skin_selector-----------------------------------------------------------------
WIDTH_BETWEEN_PLAYER = 340

# ----------------------------------------------------------------Test_field----------------------------------------------------------------
PLAYER_IFRAMES = 0.75
MAX_QUEUE = 3
SPAWN_POINTS = {"spawn1": (0, 30),
                "spawn2": (930, 30),
                "spawn3": (0, 510),
                "spawn4": (930, 510)}
PLAYER1_MOVE_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE]
PLAYER2_MOVE_KEYS  = [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_KP0]


# Player images
PLAYER1_IMAGES = {
    "idle": [
        pygame.image.load("assets/player_color/p_1_idle_0.png"),
        pygame.image.load("assets/player_color/p_1_idle_1.png"),
        pygame.image.load("assets/player_color/p_1_idle_2.png")
    ],
    "down":[
        pygame.image.load("assets/player_color/p_1_down_0.png"),
        pygame.image.load("assets/player_color/p_1_down_1.png"),
        pygame.image.load("assets/player_color/p_1_down_2.png")
    ],
    "up": [
        pygame.image.load("assets/player_color/p_1_up_0.png"),
        pygame.image.load("assets/player_color/p_1_up_1.png"),
        pygame.image.load("assets/player_color/p_1_up_2.png")
    ],
    "left": [
        pygame.image.load("assets/player_color/p_1_left_0.png"),
        pygame.image.load("assets/player_color/p_1_left_1.png"),
        pygame.image.load("assets/player_color/p_1_left_2.png")
    ],
    "right": [
        pygame.image.load("assets/player_color/p_1_right_0.png"),
        pygame.image.load("assets/player_color/p_1_right_1.png"),
        pygame.image.load("assets/player_color/p_1_right_2.png")
    ]
}
PLAYER2_IMAGES = {
    "idle": [
        pygame.image.load("assets/player_color/p_1_idle_0.png"),
        pygame.image.load("assets/player_color/p_1_idle_1.png"),
        pygame.image.load("assets/player_color/p_1_idle_2.png")
    ],
    "down":[
        pygame.image.load("assets/player_color/p_1_down_0.png"),
        pygame.image.load("assets/player_color/p_1_down_1.png"),
        pygame.image.load("assets/player_color/p_1_down_2.png")
    ],
    "up": [
        pygame.image.load("assets/player_color/p_1_up_0.png"),
        pygame.image.load("assets/player_color/p_1_up_1.png"),
        pygame.image.load("assets/player_color/p_1_up_2.png")
    ],
    "left": [
        pygame.image.load("assets/player_color/p_1_left_0.png"),
        pygame.image.load("assets/player_color/p_1_left_1.png"),
        pygame.image.load("assets/player_color/p_1_left_2.png")
    ],
    "right": [
        pygame.image.load("assets/player_color/p_1_right_0.png"),
        pygame.image.load("assets/player_color/p_1_right_1.png"),
        pygame.image.load("assets/player_color/p_1_right_2.png")
    ]
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
# ------------------------------------------------------------------Player------------------------------------------------------------------
PLAYER_MAX_HEALTH = 5
HEALTH = 3
MAX_BOMB_LIMIT = 4
CURRENTBOMB = 1
MAXBOMBS = 1
POWER = 1 
LAST_MOVE_TIME = 0
SCORE = 0
LAST_TRAP_TIME = 0 
TRAP = 8
# ------------------------------------------------------------------Power-up effects------------------------------------------------------------------
FREEZE_TIMER = 0
IFRAME_TIMER = 0
# ----------------------------------------------------------------------Animations--------------------------------------------------------------------
FRAME_INDEX = 0
# Walking animation slower
ANIM_FPS = 4          
# Idle system
AFK_DELAY = 800
# HAT ANIMATION OFFSETS - Test_field.py
GAME_HAT_OFFSETS = {
    "Crown":  (5, -10),
    "Cowboy": (5, -10),
    "Cap":    (5, -6),
    "Devil":  (15, -8),
    "Cone":   (5, -10),
    "Halo":   (5, -8),
}
HAT_ANIM_OFFSETS = {
    "idle":  [0, -1, 0],
    "down":  [0, 1, 1],
    "up":    [1, 0, 1],
    "right": [0, 0, -1],
    "left":  [0, -1, 0],
}


# ---------------------------------------------------------------Map_Selector---------------------------------------------------------------

SELECTOR_COLORS = {
    'title': (255, 255, 255),
    'text': (255, 255, 255),
    'p1': (220, 50, 50),
    'p2': (50, 50, 220),
    'highlight': (100, 255, 100),
    'map_bg': (40, 40, 50),
    'map_border': (100, 100, 100),
    'selected_border': (255, 255, 255),
    'instructions': (180, 180, 180)
}
SEL_CARD_WIDTH = 240
SEL_CARD_HEIGHT = 180
SEL_CARD_SPACING = 60

#------SKIN SELECTOR CONSTANTS------
HATS = [
    {"name": "None",      "file": None,             "offset": (0, 0)},
    {"name": "Crown",     "file": "Crown.png",      "offset": (79, -30)},
    {"name": "Halo",     "file": "Halo.png",        "offset": (79, -20)},
    {"name": "Cowboy",    "file": "Cowboy.png",     "offset": (79, -25)},
    {"name": "Devil",     "file": "Devil.png",      "offset": (79, -10)},
    {"name": "Cone",      "file": "Cone.png",       "offset": (79, -20)},
    {"name": "Cap",       "file": "Cap.png",        "offset": (79, -20)},
]
TAB_COLORS = 0
TAB_HATS   = 1
TAB_NAMES  = ["Farby", "Čiapky"]  
# Hlavné farby UI
# Panel / pozadie UI
MENU_PAPER_DARK = (211, 161, 105)      # tmavší hnedý pre panel, kontrastuje s buttonom
MENU_OUTLINE = (95, 68, 46)          # okraje panelov, decentné
MENU_TEXT = (255, 245, 235)          # svetlý text, aby bol čitateľný na tmavom pozadí
MENU_DISABLED = (140, 110, 85)       

