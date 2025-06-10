import os
import pygame.image
import config

from states.state import State
from managers.music_manager import MusicManager
from managers.state_manager import StateManager


class MainMenu(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: MainMenu")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))
        self.text_bomberman = pygame.image.load(os.path.join(game.photos_dir, "bomber-man-text.png"))
        
        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)
        self.load_music()

        # Create buttons
        self.singleplayer_button = Button(config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH - 20,
                                          config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                          config.BUTTON_WIDTH,
                                          config.BUTTON_HEIGHT,
                                          "LOCAL")
        self.multiplayer_button = Button(config.SCREEN_WIDTH // 2 + 20,
                                         config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                         config.BUTTON_WIDTH,
                                         config.BUTTON_HEIGHT,
                                         "ONLINE")
        self.settings_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT // 2 + 80,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "SETTINGS")

    def handle_events(self, event):
        """Handle button clicks."""
        if self.singleplayer_button.is_clicked():
            pygame.mixer_music.stop()
            self.state_manager.change_state("MapSelector")
        elif self.multiplayer_button.is_clicked():
            self.state_manager.change_state("MultiplayerSelector")
        elif self.settings_button.is_clicked():
            self.state_manager.change_state("Settings")

    def load_music(self):
        self.music_manager.play_music('title', 'main_menu_volume', True)

    def update(self):
        pass


    def enter_single_player(self):
        """Switch to single-player state."""
        self.exit_state()  # remove MainMenu state
        self.game.state_manager.change_state("SkinSelector")


    def render(self, screen):
        """Draw the main menu screen."""
        pygame.display.set_caption("BomberMan: MainMenu")
        screen.blit(self.bg_image, (0, 0))
        title_image = self.text_bomberman
        title_image = pygame.transform.scale(title_image, (500, 200))
        title_rect = title_image.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4))
        screen.blit(title_image, title_rect)
        
        self.singleplayer_button.draw(screen)
        self.multiplayer_button.draw(screen)
        self.settings_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        """Initialize button with position, size, and text."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.action = action

    def draw(self, screen):
        """Draw the button on screen."""
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, config.BUTTON_HOVER_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, config.COLOR_BEIGE, self.rect, border_radius=config.BUTTON_RADIUS)

        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        """Check if the button is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
