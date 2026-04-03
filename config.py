import pygame
from typing import Dict, Tuple
from managers.settings_manager import load_settings

# CONSTANTS
SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FONT_SIZE = 30
H1_SIZE = 54
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 30
BUTTON_GAP = 14
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


BG_BASE       = (10, 12, 18)
BG_PANEL      = (19, 21, 31)
BORDER_SUBTLE = (30, 34, 52)
TEXT_PRIMARY  = (232, 230, 240)
TEXT_MUTED    = (180, 185, 210)
TEXT_HINT     = (150, 155, 180)
BTN_BEIGE     = (210, 185, 145)
BG_LIST       = (13, 15, 24)
BG_ITEM_SEL   = (26, 30, 46)
BORDER_FOCUS  = (50, 55, 85)
SLIDER_TRACK  = (30, 34, 52)
SLIDER_FILL   = (210, 185, 145)
BG_TAB_BAR    = (10, 12, 20)
BG_TAB_ACTIVE = (30, 34, 54)
SCROLLBAR_TRK = (25, 28, 42)
SCROLLBAR_KNB = (60, 66, 100)
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
IDLE_INDEX = 0
IDLE_FPS = 4
TW = 36
# Layout
PANEL_W = 340
PANEL_H = 480
TOP_Y   = 55
# Výška zón vo vnútri panelu (zhora):
PREVIEW_H   = 130
TAB_H       = 36
TAB_PAD     = 8       # medzera nad tabbar
LIST_PAD    = 8       # medzera pod tabbar
HINT_H      = 48
PANEL_PAD   = 14
ROW_H       = 42
CHIP_R      = 12
# ----------------------------------------------------------------Test_field----------------------------------------------------------------
PLAYER_IFRAMES = 750
MAX_QUEUE = 3
SPAWN_POINTS = {"spawn1": (0, 30),
                "spawn2": (930, 30),
                "spawn3": (0, 510),
                "spawn4": (930, 510)}
PLAYER1_MOVE_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE]
PLAYER2_MOVE_KEYS  = [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_0]


# Player images
PLAYER1_IMAGES = {
    "idle": [
        pygame.image.load("assets/player_animations/p_1_idle_0.png"),
        pygame.image.load("assets/player_animations/p_1_idle_1.png"),
        pygame.image.load("assets/player_animations/p_1_idle_2.png")
    ],
    "down":[
        pygame.image.load("assets/player_animations/p_1_down_0.png"),
        pygame.image.load("assets/player_animations/p_1_down_1.png"),
        pygame.image.load("assets/player_animations/p_1_down_2.png")
    ],
    "up": [
        pygame.image.load("assets/player_animations/p_1_up_0.png"),
        pygame.image.load("assets/player_animations/p_1_up_1.png"),
        pygame.image.load("assets/player_animations/p_1_up_2.png")
    ],
    "left": [
        pygame.image.load("assets/player_animations/p_1_left_0.png"),
        pygame.image.load("assets/player_animations/p_1_left_1.png"),
        pygame.image.load("assets/player_animations/p_1_left_2.png")
    ],
    "right": [
        pygame.image.load("assets/player_animations/p_1_right_0.png"),
        pygame.image.load("assets/player_animations/p_1_right_1.png"),
        pygame.image.load("assets/player_animations/p_1_right_2.png")
    ]
}
PLAYER2_IMAGES = {
    "idle": [
        pygame.image.load("assets/player_animations/p_1_idle_0.png"),
        pygame.image.load("assets/player_animations/p_1_idle_1.png"),
        pygame.image.load("assets/player_animations/p_1_idle_2.png")
    ],
    "down":[
        pygame.image.load("assets/player_animations/p_1_down_0.png"),
        pygame.image.load("assets/player_animations/p_1_down_1.png"),
        pygame.image.load("assets/player_animations/p_1_down_2.png")
    ],
    "up": [
        pygame.image.load("assets/player_animations/p_1_up_0.png"),
        pygame.image.load("assets/player_animations/p_1_up_1.png"),
        pygame.image.load("assets/player_animations/p_1_up_2.png")
    ],
    "left": [
        pygame.image.load("assets/player_animations/p_1_left_0.png"),
        pygame.image.load("assets/player_animations/p_1_left_1.png"),
        pygame.image.load("assets/player_animations/p_1_left_2.png")
    ],
    "right": [
        pygame.image.load("assets/player_animations/p_1_right_0.png"),
        pygame.image.load("assets/player_animations/p_1_right_1.png"),
        pygame.image.load("assets/player_animations/p_1_right_2.png")
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
# Power-up types and properties
POWERUP_TYPES = [
    "bomb_powerup",  # Increases max bombs
    "range_powerup",  # Increases explosion range
    "freeze_powerup",  # Freezes the other player
    "live+_powerup",  # Adds an extra life
    "shield_powerup"  # Temporary invincibility
]  
FROZEN_UNTIL = 0 # Timestamp until which the player is frozen
FIELD_DURATION = 30  # Power-up remains on the field for 30 seconds
EFFECT_DURATION = 30  # Duration of effect in seconds after collection
POWERUP_SPAWNING_RATE = 0.15
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
#message timer
MESSAGE_TIMER = 0
CURRENT_FRAME_INDEX = 0
# Freeze and invincibility timers
FREEZE_TIMER = 0
IFRAME_TIMER = 0
#darkness power-up: reduces visibility for the other player for a short time
DARKNESS_TIMER = 0
FADE_ALPHA = 255
FADE_STEPS = 12
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
    "Devil":  (7, -8),
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

# ---------------------------------------------------------------Map_generator-----------------------------------------------------------------
# Konštanty
ROWS = 18
COLS = 32

# Tile hodnoty
MENU    = 3
GROUND  = 0
WALL    = 1   # unbreakable – pevná mriežka
BRICK   = 2   # breakable – náhodné
PORTAL_BLUE = 4
PORTAL_RED  = 5
SEWER   = 8

# Koľko percent voľných buniek dostane brick
BRICK_DENSITY = 0.49
# Mapy a ich pevné špeciály (portály, sewers) sú definované v map_selector.py, keďže sú úzko späté s výberom mapy.
# ── pevné pozície portálov a seweru pre každú mapu ──────────────────────────
# Formát: (row, col) – riadok 0 je menu bar
MAP_FIXED_SPECIALS = {
    "Crystal Caves": {
        "portals_blue": [(4, 28), (13, 3)],   
        "portals_red":  [(4, 3), (13, 28)], 
        "sewers": 0,
    },
    "Urban Assault": {
        "portals_blue": [],
        "portals_red":  [],
        "sewers": 1,
    },
    "Classic": {
        "portals_blue": [],
        "portals_red":  [],
        "sewers": 0,
    },
    "Ancient Ruins": {
        "portals_blue": [],
        "portals_red":  [],
        "sewers": 0,
    },
    "Desert Maze": {
        "portals_blue": [],
        "portals_red":  [],
        "sewers": 0,
    },
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
# Kartové dimenzie a rozostupy
CARD_W      = 220
CARD_H      = 160
CARD_GAP    = 24
CARD_RADIUS = 14
OVERLAY_ALPHA = 0
#------SKIN SELECTOR CONSTANTS------
BOMBS = [
    {"name": "Classic",  "file": "classic_bomb.png"},
    {"name": "Neon",     "file": "neon_bomb.png"},
    {"name": "Skull",    "file": "skull_bomb.png"},
    {"name": "Pumpkin",  "file": "pumpkin_bomb.png"},
]

EXPLOSIONS = [
    {"name": "Classic",  "file": "classic_a.png"},
    {"name": "Ice",      "file": "ice_a.png"},
    {"name": "Electric", "file": "electric_a.png"},
]
HATS = [
    {"name": "None",      "file": None,             "offset": (0, 0)},
    {"name": "Crown",     "file": "Crown.png",      "offset": (25, -15)},
    {"name": "Halo",     "file": "Halo.png",        "offset": (25, -10)},
    {"name": "Cowboy",    "file": "Cowboy.png",     "offset": (25, -15)},
    {"name": "Devil",     "file": "Devil.png",      "offset": (20, -10)},
    {"name": "Cone",      "file": "Cone.png",       "offset": (25, -20)},
    {"name": "Cap",       "file": "Cap.png",        "offset": (25, -10)},
]
TAB_COLORS = 0
TAB_HATS   = 1
TAB_BOMBS      = 2
TAB_EXPLOSIONS = 3
TAB_NAMES      = ["Colors", "Hats", "Bombs", "Explosions"] 

MENU_PAPER_DARK = (211, 161, 105)
MENU_OUTLINE = (95, 68, 46) 
MENU_TEXT = (255, 245, 235) 
MENU_DISABLED = (140, 110, 85)

AVAILABLE_COLORS = [
            WHITE_PLAYER, BLACK_PLAYER, RED_PLAYER,
            BLUE_PLAYER, DARK_GREEN_PLAYER, LIGHT_GREEN_PLAYER,
            YELLOW_PLAYER, PINK_PLAYER, ORANGE_PLAYER,
            PURPLE_PLAYER, BROWN_PLAYER, CYAN_PLAYER
        ]

AVAILABLE_HATS: Dict[str, Dict[str, str | Tuple[int, int]]] = {
    'None':     {'file': '',            'offset': (0,0)},
    'Crown':    {'file': 'Crown.png',   'offset': (5, -10)},
    'Cowboy':   {'file': 'Cowboy.png',  'offset': (5, -10)},
    'Cap':      {'file': 'Cap.png',     'offset': (5, -6)},
    'Devil':    {'file': 'Devil.png',   'offset': (15, -8)},
    'Cone':     {'file': 'Cone.png',    'offset': (5, -10)},
    'Halo':     {'file': 'Halo.png',    'offset': (5, -8)},
}

HAT_SCALE_FACTOR = 0.7
# ------------------------------------------------------------------Game_over------------------------------------------------------------------
FONT_SIZE_GAMEOVER = 22
PW = 400
PH = 260
BTN_W = 160
BTN_H = 46
GAP_X = 12
GAP_Y = 10
# ---------------------------------------------------------------Network---------------------------------------------------------------
SERVER_PORT = 9999
load_settings()