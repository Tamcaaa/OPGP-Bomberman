import socket
import pygame
import config
import os


from states.state import State
from managers.music_manager import MusicManager
from managers.state_manager import StateManager
from custom_classes.button import Button
from managers.network_manager import NetworkManager

class MultiplayerSelector(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: Multiplayer Selector")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))
        self.text_bomberman = pygame.image.load(os.path.join(game.photos_dir, "bomber-man-text.png"))

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.network_manager = NetworkManager(_socket)
        
        # Create buttons
        self.host_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH - 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Host",
            font='CaveatBrush-Regular.ttf',
            button_color=config.COLOR_BEIGE,)
        self.join_button = Button(
            config.SCREEN_WIDTH // 2 + 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Join",
            font='CaveatBrush-Regular.ttf',
            button_color=config.COLOR_BEIGE,)
        self.goBack_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT // 2 + 80,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Go Back",
            font='CaveatBrush-Regular.ttf',
            button_color=config.COLOR_BEIGE,)

    def handle_events(self, event):
        """Handle button clicks."""
        if self.host_button.is_clicked():
            self.state_manager.change_state("MultiplayerLobby","Server Host",self.network_manager,is_host=True)
        elif self.join_button.is_clicked():
            self.state_manager.change_state('InputPopup',self.network_manager)
        elif self.goBack_button.is_clicked():
            self.exit_state()
            self.state_manager.change_state("MainMenu")

    def update(self):
        pass

    def render(self, screen):
        """Draw the main menu screen."""
        pygame.display.set_caption("BomberMan: Multiplayer Selector")
        screen.blit(self.bg_image, (0, 0))

        title_image = self.text_bomberman
        title_image = pygame.transform.scale(title_image, (500, 200))
        title_rect = title_image.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4))
        screen.blit(title_image, title_rect)

        self.host_button.draw(screen)
        self.join_button.draw(screen)
        self.goBack_button.draw(screen)

