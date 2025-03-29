import pygame

import main_menu
from main_menu import MainMenu

# Constants
FONT_SIZE = 24  # Button text font size
H1_SIZE = 54  # H1 title text size
BUTTON_RADIUS = 4

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)


class BomberManApp:
    def __init__(self):
        pygame.init()

        # Basic Game Settings
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 960, 540
        self.game_canvas = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        self.font = pygame.font.Font(None, FONT_SIZE)
        self.h1_font = pygame.font.Font(None, H1_SIZE)

        self.state_stack = []

        # When initialing the class
        self.running = False

        self.load_states()

    def run(self):
        self.running = True
        while self.running:
            self.get_events()
            self.render()

    def render(self):
        # Fill screen with background image
        self.state_stack[-1].render(self.game_canvas)
        self.screen.blit(self.game_canvas, (0, 0))
        pygame.display.flip()

    def load_states(self):
        main_menu_screen = MainMenu(self)
        self.state_stack.append(main_menu_screen)

    def get_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

            if isinstance(self.state_stack[-1], main_menu.MainMenu):
                if self.state_stack[-1].singleplayer_button.is_clicked():
                    self.state_stack[-1].enter_single_player()
                elif self.state_stack[-1].multiplayer_button.is_clicked():
                    print("Multiplayer")

    def draw_text(self, screen: pygame.Surface, text: str, color: pygame.Color | tuple, x: int, y: int):
        text_surface = self.h1_font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        screen.blit(text_surface, text_rect)


# Define Button class

if __name__ == '__main__':
    app = BomberManApp()
    app.run()
    pygame.quit()
