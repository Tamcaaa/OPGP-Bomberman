import os
import pygame
import config

from states.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager
from states.map_selector import MapSelector
from states.settings import Settings


class PauseState(State):
    def __init__(self, game,map_selected,map_name):
        super().__init__(game)
        self.font = pygame.font.Font(None, 60)
        self.selected_option = 0
        self.map_selected = map_selected
        self.map_name = map_name

        # Výpočty pre zarovnanie
        left_x = 200
        bottom_y = config.SCREEN_HEIGHT - 100  
        spacing = 15
        total_height = 5 * config.BUTTON_HEIGHT + 4 * spacing
        start_y = bottom_y - total_height

        self.buttons = [
            Button(left_x, start_y + i * (config.BUTTON_HEIGHT + spacing),
                   config.BUTTON_WIDTH, config.BUTTON_HEIGHT, text,font='CaveatBrush-Regular.ttf',button_color=config.COLOR_BEIGE)
            for i, text in enumerate(["Resume", "Restart", "Map Select", "Settings", "Main Menu"])
        ]

        self.background_image = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "pause.png")).convert_alpha(),
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.mixer.music.pause()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_p, pygame.K_ESCAPE):
                self.exit_state()
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.buttons)
            elif event.key == pygame.K_RETURN:
                self.select_option()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, button in enumerate(self.buttons):
                    if button.is_clicked():
                        self.selected_option = i
                        self.select_option()

    def update(self):
        pass
    def render(self, screen):

        screen.blit(self.background_image, (0, 0))
        for button in self.buttons:
            button.draw(screen)

    def select_option(self):
        index = self.selected_option

        if index == 0:  # Resume
            self.exit_state()
        elif index == 1:  # Restart
            self.exit_state()
            self.game.state_manager.change_state("TestField",self.map_selected,self.map_name)
        elif index == 2:  # Map Select
            self.exit_state()
            self.game.state_manager.change_state("MapSelector")
        elif index == 3:  # Settings
            self.game.state_manager.change_state("Settings")
        elif index == 4:  # Main Menu
            self.exit_state()
            self.game.state_manager.change_state("MainMenu")

    def exit_state(self):
        pygame.mixer.music.unpause()
        super().exit_state()

