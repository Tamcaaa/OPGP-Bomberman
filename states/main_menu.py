import pygame.image, os
import config
from states.state import State
from states.test_field import TestField

class MainMenu(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: MainMenu")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        # Create buttons
        self.singleplayer_button = Button(config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH - 20,
                                          config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                          config.BUTTON_WIDTH,
                                          config.BUTTON_HEIGHT,
                                          "Singleplayer")
        self.multiplayer_button = Button(config.SCREEN_WIDTH // 2 + 20,
                                         config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                         config.BUTTON_WIDTH,
                                         config.BUTTON_HEIGHT,
                                         "Multiplayer")

    def handle_events(self):
        """Handle button clicks."""
        if self.singleplayer_button.is_clicked():
            self.enter_single_player()
        elif self.multiplayer_button.is_clicked():
            print("Multiplayer")

    def enter_single_player(self):
        """Switch to single-player state."""
        new_state = TestField(self.game)
        new_state.enter_state()
    
    def render(self, screen):
        """Draw the main menu screen."""
        screen.blit(self.bg_image, (0, 0))
        self.game.draw_text(screen, "BOMBER-MAN", config.BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)
        self.singleplayer_button.draw(screen)
        self.multiplayer_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        """Initialize button with position, size, and text."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action

    def draw(self, screen):
        """Draw the button on screen."""
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, config.BUTTON_HOVER_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, config.BUTTON_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)

        # Render the text on the button
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        """Check if the button is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
