import os
import pygame
import config

from states.general.state import State
from managers.music_manager import MusicManager
from custom_classes.button import Button

class GameOver(State):
    def __init__(self, game, winner, map_selected, map_name, selected_skins=None):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: GameOver")
        self.map_selected   = map_selected
        self.map_name       = map_name
        self.game           = game
        self.winner         = winner
        self.selected_skins = selected_skins or {}

        self.winner_color = (
            self.selected_skins[winner][0]
            if winner in self.selected_skins
            else config.BTN_BEIGE
        )

        try:
            self.bg = pygame.image.load(
                os.path.join(game.photos_dir, "bg.png")
            ).convert()
        except Exception:
            self.bg = None

        self.font_lg = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_md = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.font_sm = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
        self.font_xs = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        btn_w = config.BTN_W
        btn_h = config.BTN_H
        gap_x = config.GAP_X
        gap_y = config.GAP_Y
        cx    = config.SCREEN_WIDTH  // 2
        by    = config.SCREEN_HEIGHT // 2 + 50

        # 2×2 grid
        col_l = cx - btn_w - gap_x // 2
        col_r = cx + gap_x // 2
        row1  = by
        row2  = by + btn_h + gap_y

        self.retry_button = Button(
            col_l, row1, btn_w, btn_h,
            "Retry",
            font="CaveatBrush-Regular.ttf",
            font_size=config.FONT_SIZE_GAMEOVER,
            style="filled",
        )
        self.exit_button = Button(
            col_r, row1, btn_w, btn_h,
            "Exit",
            font="CaveatBrush-Regular.ttf",
            font_size=config.FONT_SIZE_GAMEOVER,
            style="outline",
        )
        self.map_select_button = Button(
            col_l, row2, btn_w, btn_h,
            "Map Select",
            font="CaveatBrush-Regular.ttf",
            font_size=config.FONT_SIZE_GAMEOVER,
            style="outline",
        )
        self.main_menu_button = Button(
            col_r, row2, btn_w, btn_h,
            "Main Menu",
            font="CaveatBrush-Regular.ttf",
            font_size=config.FONT_SIZE_GAMEOVER,
            style="outline",
        )

        self.fade_alpha = 0

        self.music_manager = MusicManager()
        self.load_music()

    def load_music(self):
        self.music_manager.play_music('game_over', 'game_over_volume', True)

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
        if self.retry_button.is_clicked():
            pygame.mixer_music.stop()
            self.enter_single_player()
        elif self.exit_button.is_clicked():
            pygame.mixer_music.stop()
            self.music_manager.play_music('title', 'main_menu_volume', True)
            self.exit_state()
            self.exit_state()
        elif self.map_select_button.is_clicked():
            pygame.mixer_music.stop()
            self.music_manager.play_music('title', 'main_menu_volume', True)
            self.exit_state()
            self.game.state_manager.change_state("MapSelector")
        elif self.main_menu_button.is_clicked():
            pygame.mixer_music.stop()
            self.music_manager.play_music('title', 'main_menu_volume', True)
            self.exit_state()
            self.game.state_manager.change_state("MainMenu")

    def enter_single_player(self):
        self.exit_state()
        self.game.state_manager.change_state("TestField", self.map_selected, self.map_name)

    # ------------------------------------------------------------------ render
    def render(self, screen):
        self.fade_alpha = min(self.fade_alpha + 8, 255)

        screen.fill(config.BG_BASE)
        if self.bg:
            bg_s = pygame.transform.scale(self.bg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            dark = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            dark.fill((10, 12, 18, 180))
            screen.blit(bg_s, (0, 0))
            screen.blit(dark, (0, 0))

        if self.fade_alpha < 255:
            fade = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((10, 12, 18, 255 - self.fade_alpha))
            screen.blit(fade, (0, 0))

        cx = config.SCREEN_WIDTH  // 2
        cy = config.SCREEN_HEIGHT // 2

        # Centrálny panel
        pw, ph = config.PW, config.PH
        panel  = pygame.Rect(cx - pw // 2, cy - ph // 2 - 30, pw, ph)
        self._draw_rrect(screen, config.BG_PANEL, panel, radius=18, alpha=220,
                         border=1, border_color=self.winner_color)
        self._glow_line(screen, panel, self.winner_color, alpha=100)

        # "GAME OVER"
        self._text(screen, "GAME OVER", self.font_lg, self.winner_color,
                   (cx, panel.y + 22), align="center")

        # Oddeľovač
        sep = pygame.Surface((pw - 40, 1), pygame.SRCALPHA)
        sep.fill((*config.BORDER_SUBTLE, 180))
        screen.blit(sep, (cx - (pw - 40) // 2, panel.y + 62))

        # Winner text
        winner_text = f"PLAYER {self.winner} WINS"
        self._text(screen, winner_text, self.font_md, self.winner_color,
                   (cx, panel.y + 76), align="center")

        # Mapa
        map_text = f"map: {self.map_name}"
        self._text(screen, map_text, self.font_xs, config.TEXT_MUTED,
                   (cx, panel.y + 112), align="center")

        # Subtitle hint
        self._text(screen, "BOMBERMAN", self.font_xs, config.TEXT_HINT,
                   (cx, panel.y + 140), align="center")

        # Tlačidlá
        self.retry_button.draw(screen)
        self.exit_button.draw(screen)
        self.map_select_button.draw(screen)
        self.main_menu_button.draw(screen)