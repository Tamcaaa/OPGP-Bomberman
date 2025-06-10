import pygame
import config
import os

from states.state import State
from managers.music_manager import MusicManager
from managers.state_manager import StateManager


class MultiplayerSelector(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: MultiplayerSelector")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)

        # Create buttons
        self.host_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH - 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Host")
        self.join_button = Button(
            config.SCREEN_WIDTH // 2 + 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Join")
        self.goBack_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT // 2 + 80,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Go Back")

    def handle_events(self, event):
        """Handle button clicks."""
        if self.host_button.is_clicked():
            print("host")
        elif self.join_button.is_clicked():
            print("join")
        elif self.goBack_button.is_clicked():
            self.exit_state()
            self.state_manager.change_state("MainMenu")

    def update(self):
        pass

    def render(self, screen):
        """Draw the main menu screen."""
        pygame.display.set_caption("BomberMan: MultiplayerSelector")
        screen.blit(self.bg_image, (0, 0))
        self.game.draw_text(screen, "BOMBER-MAN", config.COLOR_BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)
        self.host_button.draw(screen)
        self.join_button.draw(screen)
        self.goBack_button.draw(screen)


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
