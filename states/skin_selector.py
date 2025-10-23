import pygame, os
from states.state import State
import config
from managers.state_manager import StateManager

AVAILABLE_COLORS = {
    config.WHITE_PLAYER: "White",
    config.BLACK_PLAYER: "Black",
    config.RED_PLAYER: "Red",
    config.BLUE_PLAYER: "Blue",
    config.GREEN_PLAYER: "Green",
    config.YELLOW_PLAYER: "Yellow",
}

class SkinSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Skin Selection")
        self.state_manager = StateManager(self.game)
        
        self.bg = pygame.image.load(os.path.join(game.photos_dir, "battlefield-bg.png")).convert()
        
        # Načtení základního sprite hráče pro náhled barvy
        self.base_player_img = pygame.image.load(
            os.path.join(game.photos_dir, "player_color", "p_1_idle_0.png")
        ).convert_alpha()

        # Zvětšení náhledu
        w, h = self.base_player_img.get_size()
        self.base_player_img = pygame.transform.scale(self.base_player_img, (w * 8, h * 8))
        
        # Úložiště vybraných barev hráčů
        self.players = {1: None, 2: None}

        # Index vybrané barvy pro každého hráče
        self.selected_index = {1: 0, 2: 0}

        # UI nastavení
        self.font = pygame.font.Font("CaveatBrush-Regular.ttf", 28)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.circle_radius = 20
        self.circle_spacing = 50
        self.side_margin = 50

        # Ovládání
        self.controls = {
            1: {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'select': pygame.K_RETURN},
            2: {'up': pygame.K_w, 'down': pygame.K_s, 'select': pygame.K_LSHIFT},
        }

    def tint_image(self, image, color):
        """Aplikuje barvu na sprite hráče."""
        tinted = image.copy()
        tinted.fill(color, special_flags=pygame.BLEND_MULT)
        return tinted

    def draw(self, screen):
        color_keys = list(AVAILABLE_COLORS.keys())
        y_start = 100

        # Player 1 - levá strana
        for idx, color in enumerate(color_keys):
            x = self.side_margin
            y = y_start + idx * self.circle_spacing
            color_draw = (80, 80, 80) if self.players[2] == color else color
            pygame.draw.circle(screen, color_draw, (x, y), self.circle_radius)
            if self.selected_index[1] == idx:
                pygame.draw.circle(screen, (200, 50, 50), (x, y), self.circle_radius, 3)

        # Player 2 - pravá strana
        for idx, color in enumerate(color_keys):
            x = config.SCREEN_WIDTH - self.side_margin
            y = y_start + idx * self.circle_spacing
            color_draw = (80, 80, 80) if self.players[1] == color else color
            pygame.draw.circle(screen, color_draw, (x, y), self.circle_radius)
            if self.selected_index[2] == idx:
                pygame.draw.circle(screen, (50, 150, 250), (x, y), self.circle_radius, 3)

        # Text instrukcí
        p1_text = "Player 1: Up/Down arrows, ENTER to select"
        p2_text = "Player 2: W/S keys, LSHIFT to select"
        if self.players[1]:
            p1_text = f"Player 1: {AVAILABLE_COLORS[self.players[1]]} selected!"
        if self.players[2]:
            p2_text = f"Player 2: {AVAILABLE_COLORS[self.players[2]]} selected!"

        screen.blit(self.info_font.render(p1_text, True, (200, 50, 50)), (50, config.SCREEN_HEIGHT - 80))
        p2_text_surf = self.info_font.render(p2_text, True, (50, 150, 250))
        screen.blit(p2_text_surf, (config.SCREEN_WIDTH - 50 - self.info_font.size(p2_text)[0], config.SCREEN_HEIGHT - 80))

        # --- Náhled hráčů ---
        p1_x, p1_y = 80, 110
        p2_x, p2_y = config.SCREEN_WIDTH - config.WIDTH_BETWEEN_PLAYER, 110

        p1_color = color_keys[self.selected_index[1]]
        p2_color = color_keys[self.selected_index[2]]

        p1_img = self.tint_image(self.base_player_img, p1_color)
        p2_img = self.tint_image(self.base_player_img, p2_color)

        

        screen.blit(p1_img, (p1_x, p1_y))
        screen.blit(p2_img, (p2_x, p2_y))

        pygame.display.flip()

    def handle_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        color_keys = list(AVAILABLE_COLORS.keys())

        # Player 1
        if event.key == self.controls[1]['up']:
            self.selected_index[1] = (self.selected_index[1] - 1) % len(color_keys)
        elif event.key == self.controls[1]['down']:
            self.selected_index[1] = (self.selected_index[1] + 1) % len(color_keys)
        elif event.key == self.controls[1]['select']:
            chosen = color_keys[self.selected_index[1]]
            if self.players[2] != chosen:
                self.players[1] = chosen

        # Player 2
        if event.key == self.controls[2]['up']:
            self.selected_index[2] = (self.selected_index[2] - 1) % len(color_keys)
        elif event.key == self.controls[2]['down']:
            self.selected_index[2] = (self.selected_index[2] + 1) % len(color_keys)
        elif event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
            chosen = color_keys[self.selected_index[2]]
            if self.players[1] != chosen:
                self.players[2] = chosen

        # Pokračovat, pokud oba hráči vybrali
        if all(self.players.values()):
            from states.map_selector import MapSelector
            self.state_manager.change_state("MapSelector", self.players)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))
        self.draw(screen)
