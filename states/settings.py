import pygame
import config
from states.state import State

class Settings(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Settings")
        self.font = pygame.font.Font(None, config.FONT_SIZE)

        self.volume = game.settings.get("volume", 0.5)
        self.last_volume = self.volume if self.volume > 0.0 else 0.5

        # Buttons
        self.back_button = Button(20, config.SCREEN_HEIGHT - 70, 150, 50, "Back")
        self.volume_up_button = Button(330, 200, 50, 50, "+")
        self.volume_down_button = Button(220, 200, 50, 50, "-")
        self.mute_button = Button(220, 300, 150, 50, "Mute" if self.volume > 0.0 else "Unmute")

    def handle_events(self, event):
        if self.back_button.is_clicked():
            self.exit_state()
        elif self.volume_up_button.is_clicked():
            self.volume = min(1.0, self.volume + 0.1)
            self.last_volume = self.volume
            pygame.mixer.music.set_volume(self.volume)
            self.mute_button.text = "Mute"
            self.game.settings["volume"] = self.volume
        elif self.volume_down_button.is_clicked():
            self.volume = max(0.0, self.volume - 0.1)
            if self.volume > 0.0:
                self.last_volume = self.volume
                self.mute_button.text = "Mute"
            else:
                self.mute_button.text = "Unmute"
            pygame.mixer.music.set_volume(self.volume)
            self.game.settings["volume"] = self.volume
        elif self.mute_button.is_clicked():
            if self.volume > 0.0:
                self.last_volume = self.volume
                self.volume = 0.0
                self.mute_button.text = "Unmute"
            else:
                self.volume = self.last_volume
                self.mute_button.text = "Mute"
            pygame.mixer.music.set_volume(self.volume)
            self.game.settings["volume"] = self.volume

    def render(self, screen):
        screen.fill((30, 30, 30))

        # Draw buttons
        self.back_button.draw(screen)
        self.volume_up_button.draw(screen)
        self.volume_down_button.draw(screen)
        self.mute_button.draw(screen)

        # Volume text
        vol_text = self.font.render(f"Volume: {int(self.volume * 100)}%", True, config.TEXT_COLOR)
        screen.blit(vol_text, (200, 150))

        # Mute status text
        if self.volume == 0.0:
            mute_text = self.font.render("Sound Muted", True, config.TEXT_COLOR)
            screen.blit(mute_text, (config.SCREEN_WIDTH // 2, 350))


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = config.BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]
