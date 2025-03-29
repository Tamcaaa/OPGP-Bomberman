import pygame.image

from state import State
from test_field import TestField


class MainMenu(State):
    def __init__(self, game):
        State.__init__(self, game)

        # CONSTANTS
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 960, 540
        self.BUTTON_WIDTH, self.BUTTON_HEIGHT = 150, 40

        pygame.display.set_caption("BomberMan: MainMenu")

        self.bg_image = pygame.image.load("photos/bg.png")

        #
        self.singleplayer_button = Button(self.SCREEN_WIDTH // 2 - self.BUTTON_WIDTH - 20,
                                          self.SCREEN_HEIGHT // 2 - self.BUTTON_HEIGHT // 2,
                                          self.BUTTON_WIDTH,
                                          self.BUTTON_HEIGHT,
                                          "Singleplayer", )
        self.multiplayer_button = Button(self.SCREEN_WIDTH // 2 + 20,
                                         self.SCREEN_HEIGHT // 2 - self.BUTTON_HEIGHT // 2,
                                         self.BUTTON_WIDTH,
                                         self.BUTTON_HEIGHT,
                                         "Multiplayer")

    def enter_single_player(self):
        new_state = TestField(self.game)
        new_state.enter_state()

    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))
        self.game.draw_text(screen, "BOMBER-MAN", (0, 0, 0), self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 4)
        self.singleplayer_button.draw(screen)
        self.multiplayer_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None, ):
        # CONSTANTS
        self.FONT_SIZE = 24
        self.BUTTON_COLOR = (88, 94, 149)
        self.BUTTON_HOVER_COLOR = (0, 100, 200)
        self.BUTTON_RADIUS = 4
        self.TEXT_COLOR = (255, 255, 255)

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, self.FONT_SIZE)
        self.action = action

    def draw(self, screen):
        # Render the text on the button
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, self.BUTTON_HOVER_COLOR, self.rect, border_radius=self.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, self.BUTTON_COLOR, self.rect, border_radius=self.BUTTON_RADIUS)

        text_surface = self.font.render(self.text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        # Check if the button is clicked
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False
