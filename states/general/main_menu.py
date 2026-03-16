import os
import pygame
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

        try:
            self.bg_image = pygame.image.load(
                os.path.join(game.photos_dir, "bg.png")
            ).convert()
        except Exception:
            self.bg_image = None

        # Title image – zachovaný, ale použijeme ako fallback
        try:
            self.text_bomberman = pygame.image.load(
                os.path.join(game.photos_dir, "bomber-man-text.png")
            ).convert_alpha()
        except Exception:
            self.text_bomberman = None

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)
        self.load_music()

        # Fonty
        self.font_lg = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_md = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.font_xs = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        # Fade-in
        self.fade_alpha = 255

        # Layout tlačidiel – stĺpec vycentrovaný
        btn_w  = config.BUTTON_WIDTH
        btn_h  = config.BUTTON_HEIGHT
        gap    = 14
        cx     = config.SCREEN_WIDTH // 2
        # 3 tlačidlá pod sebou, vycentrované
        total_h = btn_h * 3 + gap * 2
        by      = config.SCREEN_HEIGHT // 2 + 20

        self.singleplayer_button = Button(
            cx - btn_w // 2, by,
            btn_w, btn_h, "LOCAL",
            font="CaveatBrush-Regular.ttf",
            style="filled",
        )
        self.multiplayer_button = Button(
            cx - btn_w // 2, by + btn_h + gap,
            btn_w, btn_h, "ONLINE",
            font="CaveatBrush-Regular.ttf",
            style="outline",
        )
        self.settings_button = Button(
            cx - btn_w // 2, by + (btn_h + gap) * 2,
            btn_w, btn_h, "SETTINGS",
            font="CaveatBrush-Regular.ttf",
            style="outline",
        )

    # ------------------------------------------------------------------ helpers
    def _draw_rrect(self, surf, color, rect, radius=14, alpha=255, border=0, border_color=None):
        if alpha < 255:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color[:3], alpha), s.get_rect(), border_radius=radius)
            if border and border_color:
                pygame.draw.rect(s, (*border_color[:3], min(alpha + 40, 255)),
                                 s.get_rect(), width=border, border_radius=radius)
            surf.blit(s, rect.topleft)
        else:
            pygame.draw.rect(surf, color, rect, border_radius=radius)
            if border and border_color:
                pygame.draw.rect(surf, border_color, rect, width=border, border_radius=radius)

    def _text(self, surf, text, font, color, pos, align="left"):
        rendered = font.render(text, True, color)
        x, y = pos
        if align == "center":
            x -= rendered.get_width() // 2
        elif align == "right":
            x -= rendered.get_width()
        shadow = font.render(text, True, (0, 0, 0))
        surf.blit(shadow, (x + 1, y + 1))
        surf.blit(rendered, (x, y))

    def _glow_line(self, screen, rect, color, alpha=60):
        glow = pygame.Surface((rect.width, 6), pygame.SRCALPHA)
        for gx in range(rect.width):
            a = int(alpha * (1 - abs(gx - rect.width / 2) / (rect.width / 2)))
            pygame.draw.line(glow, (*color, a), (gx, 0), (gx, 5))
        screen.blit(glow, (rect.x, rect.y))

    # ------------------------------------------------------------------ events
    def handle_events(self, event):
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
        self.exit_state()
        self.game.state_manager.change_state("SkinSelector")

    # ------------------------------------------------------------------ render
    def render(self, screen):
        pygame.display.set_caption("BomberMan: MainMenu")

        # Fade-in
        self.fade_alpha = max(self.fade_alpha - 8, 0)

        # Pozadie
        screen.fill(config.BG_BASE)
        if self.bg_image:
            bg_s = pygame.transform.scale(
                self.bg_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )
            dark = pygame.Surface(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            dark.fill((10, 12, 18, 180))
            screen.blit(bg_s, (0, 0))
            screen.blit(dark, (0, 0))

        cx = config.SCREEN_WIDTH // 2

        # Title image – presne ako v origináli
        if self.text_bomberman:
            title_image = pygame.transform.scale(self.text_bomberman, (500, 200))
            title_rect  = title_image.get_rect(center=(cx, config.SCREEN_HEIGHT // 4))
            screen.blit(title_image, title_rect)

        # Tlačidlá
        self.singleplayer_button.draw(screen)
        self.multiplayer_button.draw(screen)
        self.settings_button.draw(screen)

        # Verzia / hint dole
        self._text(screen, "© 2025  BOMBERMAN", self.font_xs, config.TEXT_HINT,
                   (cx, config.SCREEN_HEIGHT - 22), align="center")

        # Fade-in overlay
        if self.fade_alpha > 0:
            fade = pygame.Surface(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            fade.fill((10, 12, 18, self.fade_alpha))
            screen.blit(fade, (0, 0))
