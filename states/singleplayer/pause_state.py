import os
import pygame
import config

from states.general.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager

class PauseState(State):
    def __init__(self, game, map_selected, map_name):
        super().__init__(game)
        self.map_selected = map_selected
        self.map_name     = map_name
        self.selected_option = 0
        self.music_manager = MusicManager()

        # Fonty
        self.font_lg = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_xs = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        # Ulož stav hudby
        self.prev_music_playing = pygame.mixer.music.get_busy()
        if self.prev_music_playing:
            pygame.mixer.music.pause()
        self.load_music()

        # Tlačidlá – stĺpec v paneli
        btn_w   = config.BUTTON_WIDTH
        btn_h   = config.BUTTON_HEIGHT
        gap     = 14
        labels  = ["Resume", "Restart", "Map Select", "Settings", "Main Menu"]
        styles  = ["filled", "outline", "outline", "outline", "outline"]

        # Panel rozmery
        self.PANEL_W = btn_w + 48
        self.PANEL_H = btn_h * len(labels) + gap * (len(labels) - 1) + 80
        self.panel_x = config.SCREEN_WIDTH  // 2 - self.PANEL_W // 2
        self.panel_y = config.SCREEN_HEIGHT // 2 - self.PANEL_H // 2

        bx = self.panel_x + 24
        by = self.panel_y + 48

        self.buttons = [
            Button(bx, by + i * (btn_h + gap), btn_w, btn_h, text,
                   font="CaveatBrush-Regular.ttf", style=style)
            for i, (text, style) in enumerate(zip(labels, styles))
        ]

        # Pozadie (voliteľné)
        try:
            self.background_image = pygame.transform.scale(
                pygame.image.load(os.path.join("assets", "pause.png")).convert_alpha(),
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )
        except Exception:
            self.background_image = None

    def load_music(self):
        self.music_manager.play_music('pause', 'main_menu_volume', loop=True)

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

    # ------------------------------------------------------------------ render
    def render(self, screen):
        # Pozadie hry (blurred efekt cez tmavý overlay)
        if self.background_image:
            screen.blit(self.background_image, (0, 0))

        # Tmavý overlay
        overlay = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((10, 12, 18, 180))
        screen.blit(overlay, (0, 0))

        # Panel
        panel = pygame.Rect(self.panel_x, self.panel_y, self.PANEL_W, self.PANEL_H)
        self._draw_rrect(screen, config.BG_PANEL, panel, radius=18, alpha=230,
                         border=1, border_color=config.BTN_BEIGE)
        self._glow_line(screen, panel, config.BTN_BEIGE, alpha=80)

        # "PAUSED" nadpis
        self._text(screen, "PAUSED", self.font_lg, config.BTN_BEIGE,
                   (self.panel_x + self.PANEL_W // 2, self.panel_y + 12), align="center")

        # Oddeľovač
        sep = pygame.Surface((self.PANEL_W - 40, 1), pygame.SRCALPHA)
        sep.fill((*config.BORDER_SUBTLE, 180))
        screen.blit(sep, (self.panel_x + 20, self.panel_y + 42))

        # Tlačidlá
        for button in self.buttons:
            button.draw(screen)

    # ------------------------------------------------------------------ select
    def select_option(self):
        index = self.selected_option
        if index == 0:    # Resume
            self.exit_state()
        elif index == 1:  # Restart
            self.exit_state()
            self.game.state_manager.change_state("TestField", self.map_selected, self.map_name)
        elif index == 2:  # Map Select
            self.exit_state()
            self.game.state_manager.change_state("MapSelector")
        elif index == 3:  # Settings
            self.game.state_manager.change_state("Settings")
        elif index == 4:  # Main Menu
            self.exit_state()
            self.game.state_manager.change_state("MainMenu")

    def exit_state(self):
        if self.prev_music_playing:
            self.music_manager.play_music('level', 'level_volume', True)
        super().exit_state()
