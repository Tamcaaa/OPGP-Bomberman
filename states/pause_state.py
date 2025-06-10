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

        # Výpočty pre zarovnanie
        center_x = config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2
        center_y = config.SCREEN_HEIGHT // 2
        spacing = 20  # medzera medzi tlačidlami

        total_height = 3 * config.BUTTON_HEIGHT + 2 * spacing
        start_y = center_y - total_height // 2

        self.resume_button = Button(
            center_x,
            start_y,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Resume"
        )
        self.retry_button = Button(
            center_x,
            start_y + config.BUTTON_HEIGHT + spacing,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Restart"
        )
        self.exit_button = Button(
            center_x,
            start_y + 2 * (config.BUTTON_HEIGHT + spacing),
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Main Menu"
        )

        # Načítanie obrázku pozadia
        self.background_image = pygame.image.load(os.path.join("assets", "pause.png")).convert_alpha()

        # Pauza hudby pri aktivácii pauzy
        pygame.mixer.music.pause()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                self.exit_state()
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 3
            elif event.key == pygame.K_RETURN:
                self.select_option()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ľavé tlačidlo myši
                if self.resume_button.is_hovered():
                    self.exit_state()
                elif self.retry_button.is_hovered():
                    self.exit_state()
                    self.game.state_manager.change_state("TestField")
                elif self.exit_button.is_hovered():
                    self.exit_state()
                    self.game.state_manager.change_state("MainMenu")

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.set_highlighted(self.resume_button.is_hovered(mouse_pos))
        self.retry_button.set_highlighted(self.retry_button.is_hovered(mouse_pos))
        self.exit_button.set_highlighted(self.exit_button.is_hovered(mouse_pos))

    def render(self, screen):
        screen.blit(self.background_image, (0, 0))
        text_surface = self.font.render("PAUSED", True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4))
        screen.blit(text_surface, text_rect)

        self.resume_button.draw(screen)
        self.retry_button.draw(screen)
        self.exit_button.draw(screen)

    def select_option(self):
        if self.selected_option == 0:
            self.exit_state()
        elif self.selected_option == 1:
            self.exit_state()
        elif self.retry_button.is_clicked():
            self.enter_single_player()        
        elif self.selected_option == 2:
            self.exit_state()
            self.game.state_manager.change_state("MainMenu")

    def exit_state(self):
        """Obnoví hudbu pri opustení pauzy."""
        pygame.mixer.music.unpause()
        super().exit_state()


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action
        self.highlighted = False

    def draw(self, screen):
        color = config.BUTTON_HOVER_COLOR if self.highlighted else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)

        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def set_highlighted(self, highlighted):
        self.highlighted = highlighted

    def is_hovered(self, pos=None):
        if pos is None:
            pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(pos)
