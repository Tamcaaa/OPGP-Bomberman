import os
import pygame.image
import config

from states.state import State
from managers.music_manager import MusicManager
from custom_classes.button import Button

class MultiplayerGameOver(State):
    def __init__(self, game, winner,map_name,socket):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: GameOver")
        self.map_name = map_name
        self.socket = socket
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))
        self.winner = winner

        # Create buttons
        self.exit_button = Button(config.SCREEN_WIDTH // 2 - 20,
                                  config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
                                  config.BUTTON_WIDTH,
                                  config.BUTTON_HEIGHT,
                                  "Exit",
                                  font = 'CaveatBrush-Regular.ttf',
                                  button_color = config.COLOR_BEIGE,)
        self.music_manager = MusicManager()
        self.load_music()

    def load_music(self):
        self.music_manager.play_music('game_over', 'game_over_volume', True)

    def handle_events(self, event):
        if self.exit_button.is_clicked():
            pygame.mixer_music.stop()
            self.music_manager.play_music('title', 'main_menu_volume', True)
            self.exit_state()
            self.exit_state()
            self.socket.close()
    def render(self, screen):
        """Draw the main menu screen."""
        screen.blit(self.bg_image, (0, 0))
        self.game.draw_text(screen, "GAME OVER", config.COLOR_BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)
        self.game.draw_text(screen, f"{self.winner} won!", config.COLOR_BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 3)
        self.exit_button.draw(screen)


