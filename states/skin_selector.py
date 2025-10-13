import pygame, os
from states.state import State
import config
from managers.state_manager import StateManager

AVAILABLE_COLORS = ["white", "black", "red", "blue", "green", "yellow"]

class SkinSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Skin Selection")
        self.state_manager = StateManager(self.game)
        
        self.bg = pygame.image.load(os.path.join(game.photos_dir, "battlefield-bg.png"))
        # Player color storage
        self.players = {1: None, 2: None}

        # Selection index per player
        self.selected_index = {1: 0, 2: 0}

        # UI
        self.font = pygame.font.Font("CaveatBrush-Regular.ttf", 28)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.circle_radius = 20
        self.circle_spacing = 50
        self.side_margin = 50

        # Controls
        self.controls = {
            1: {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'select': pygame.K_RETURN},
            2: {'up': pygame.K_w, 'down': pygame.K_s, 'select': pygame.K_LSHIFT},
        }

    def draw(self, screen):
        y_start = 100

        # Player 1 left side
        for idx, color in enumerate(AVAILABLE_COLORS):
            x = self.side_margin
            y = y_start + idx * self.circle_spacing
            # stmavenie, ak farbu už zvolil druhý hráč
            if self.players[2] == color:
                color_draw = (80, 80, 80)
            else:
                color_draw = pygame.Color(color)
            pygame.draw.circle(screen, color_draw, (x, y), self.circle_radius)
            if self.selected_index[1] == idx:
                pygame.draw.circle(screen, (200, 50, 50), (x, y), self.circle_radius, 3)

        # Player 2 right side
        for idx, color in enumerate(AVAILABLE_COLORS):
            x = config.SCREEN_WIDTH - self.side_margin
            y = y_start + idx * self.circle_spacing
            # stmavenie, ak farbu už zvolil prvý hráč
            if self.players[1] == color:
                color_draw = (80, 80, 80)
            else:
                color_draw = pygame.Color(color)
            pygame.draw.circle(screen, color_draw, (x, y), self.circle_radius)
            if self.selected_index[2] == idx:
                pygame.draw.circle(screen, (50, 150, 250), (x, y), self.circle_radius, 3)

        # Instructions
        text_y = 20
        p1_text = "Player 1: Up, Down arrows to move, ENTER to select"
        p2_text = "Player 2: W S to move, LSHIFT to select"

        if self.players[1]:
            p1_text = f"Player 1: {self.players[1].upper()} selected!"
        if self.players[2]:
            p2_text = f"Player 2: {self.players[2].upper()} selected!"

        screen.blit(self.info_font.render(p1_text, True, (200, 50, 50)), (50, config.SCREEN_HEIGHT - 80))
        p2_text_surf = self.info_font.render(p2_text, True, (50, 150, 250))
        screen.blit(p2_text_surf, (config.SCREEN_WIDTH - 50 - self.info_font.size(p2_text)[0], config.SCREEN_HEIGHT - 80))

        pygame.display.flip()

    def handle_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Player 1 controls
        if event.key == self.controls[1]['up']:
            self.selected_index[1] = (self.selected_index[1] - 1) % len(AVAILABLE_COLORS)
        elif event.key == self.controls[1]['down']:
            self.selected_index[1] = (self.selected_index[1] + 1) % len(AVAILABLE_COLORS)
        elif event.key == self.controls[1]['select']:
            chosen = AVAILABLE_COLORS[self.selected_index[1]]
            if self.players[2] != chosen:
                self.players[1] = chosen

        # Player 2 controls (ľavý alebo pravý SHIFT)
        if event.key == self.controls[2]['up']:
            self.selected_index[2] = (self.selected_index[2] - 1) % len(AVAILABLE_COLORS)
        elif event.key == self.controls[2]['down']:
            self.selected_index[2] = (self.selected_index[2] + 1) % len(AVAILABLE_COLORS)
        elif event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
            chosen = AVAILABLE_COLORS[self.selected_index[2]]
            if self.players[1] != chosen:
                self.players[2] = chosen

        # Both players selected → go to MapSelector
        if all(self.players.values()):
            from states.map_selector import MapSelector
            self.state_manager.change_state(
                "MapSelector",
                self.players
            )

    def render(self, screen):
        screen.blit(self.bg, (0, 0))
        self.draw(screen)