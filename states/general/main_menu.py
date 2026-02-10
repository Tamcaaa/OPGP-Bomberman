import os
import pygame.image
import config

from states.general.state import State
from managers.music_manager import MusicManager
from managers.state_manager import StateManager
from custom_classes.button import Button

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
                                          "LOCAL",
                                          font='CaveatBrush-Regular.ttf',
                                          button_color=config.COLOR_BEIGE,)
        self.multiplayer_button = Button(config.SCREEN_WIDTH // 2 + 20,
                                         config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                         config.BUTTON_WIDTH,
                                         config.BUTTON_HEIGHT,
                                         "ONLINE",
                                         font='CaveatBrush-Regular.ttf',
                                         button_color=config.COLOR_BEIGE,)
        self.settings_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT // 2 + 80,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "SETTINGS",
            font='CaveatBrush-Regular.ttf',
            button_color=config.COLOR_BEIGE,)

    def handle_events(self, event):
        """Handle button clicks."""
        if self.singleplayer_button.is_clicked():
            self.enter_single_player()
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
