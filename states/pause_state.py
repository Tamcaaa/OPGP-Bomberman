import os
import pygame
import config

from states.state import State
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
        center_x = config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2
        center_y = config.SCREEN_HEIGHT // 2
        spacing = 20
        total_height = 5 * config.BUTTON_HEIGHT + 4 * spacing
        start_y = center_y - total_height // 2

        self.buttons = [
            Button(center_x, start_y + i * (config.BUTTON_HEIGHT + spacing),
                   config.BUTTON_WIDTH, config.BUTTON_HEIGHT, text)
            for i, text in enumerate(["Resume", "Restart", "Map Select", "Settings", "Main Menu"])
        ]

        self.background_image = pygame.image.load(os.path.join("assets", "pause.png")).convert_alpha()
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
        mouse_pos = pygame.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            button.highlighted = button.is_hovered(mouse_pos) or i == self.selected_option

    def render(self, screen):
        screen.blit(self.background_image, (0, 0))

        title = self.font.render("PAUSED", True, config.TEXT_COLOR)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4))
        screen.blit(title, title_rect)

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


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        """Initialize button with position, size, and text."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action
        self.highlighted = False

    def draw(self, screen):
        """Draw the button on screen."""
        mouse_pos = pygame.mouse.get_pos()
        color = config.BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) or self.highlighted else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)

        # Render the text on the button
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos=None):
        """Check if the mouse is over the button."""
        if pos is None:
            pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(pos)

    def is_clicked(self):
        """Check if the button is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
