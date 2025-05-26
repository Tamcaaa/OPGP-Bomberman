import os
import pygame.image
import config

from states.state import State
from managers.music_manager import MusicManager


class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 36)
        self.selected_option = 0

        self.resume_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH - 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Resume"
        )
        self.restart_button = Button(
            config.SCREEN_WIDTH // 2 + 20,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2 + 60,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Restart"
        )
        self.exit_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT // 2 - config.BUTTON_HEIGHT // 2 + 120,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Main Menu"
        )

    def handle_events(self, event):
        """Spracovanie udalostí ako stlačenia klávesov alebo kliknutia myši."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.exit_state()
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 3
            elif event.key == pygame.K_RETURN:
                self.select_option()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.resume_button.is_clicked():
                self.exit_state()
            elif self.restart_button.is_clicked():
                self.game.state_manager.change_state("TestField")
                self.exit_state()
            elif self.exit_button.is_clicked():
                self.game.state_manager.change_state("MainMenu")
                self.exit_state()

    def update(self):
        """Pauza stav nezmení nič v hre."""
        pass

    def render(self, screen):
        """Renderovanie pauzového menu."""
        overlay = pygame.Surface((self.game.screen.get_width(), self.game.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pause_text = self.font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(
            center=(self.game.screen.get_width() // 2, self.game.screen.get_height() // 2 - 100)
        )
        screen.blit(pause_text, pause_rect)

        self.render_buttons(screen)

    def render_buttons(self, screen):
        """Zobrazenie tlačidiel a zvýraznenie vybraného."""
        self.resume_button.draw(screen)
        self.restart_button.draw(screen)
        self.exit_button.draw(screen)

        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.set_highlighted(self.resume_button.rect.collidepoint(mouse_pos))
        self.restart_button.set_highlighted(self.restart_button.rect.collidepoint(mouse_pos))
        self.exit_button.set_highlighted(self.exit_button.rect.collidepoint(mouse_pos))

    def select_option(self):
        """Vykoná akciu na základe vybranej možnosti."""
        if self.selected_option == 0:
            self.exit_state()
        elif self.selected_option == 1:
            self.game.state_manager.change_state("TestField")
            self.exit_state()
        elif self.selected_option == 2:
            self.game.state_manager.change_state("MainMenu")
            self.exit_state()


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        """Inicializuj tlačidlo s pozíciou, veľkosťou a textom."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action
        self.highlighted = False

    def draw(self, screen):
        """Vykresli tlačidlo na obrazovke."""
        color = config.BUTTON_HOVER_COLOR if self.highlighted else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)

        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def set_highlighted(self, highlighted):
        """Zvýrazni tlačidlo."""
        self.highlighted = highlighted

    def is_clicked(self):
        """Skontroluj, či bolo tlačidlo stlačené."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
