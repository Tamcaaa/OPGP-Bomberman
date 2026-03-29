import config
import os
import pygame
from managers.state_manager import StateManager
from states.general.state import State
from managers.music_manager import MusicManager


class BomberManApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.fullscreen = False
        self.game_canvas = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.h1_font = pygame.font.Font(None, config.H1_SIZE)
        self.state_stack = []
        self.running = False
        self.photos_dir = os.path.join("assets")
        self.state_manager = StateManager(self)
        self.load_states()
        self.all_sprites = pygame.sprite.Group()
        self.settings = {
            "volume": 0.5,
        }

        # HUD font
        self._hud_font = pygame.font.SysFont("segoeui", 13)

        # Fullscreen tlačidlo (pravý dolný roh)
        self._btn_w   = 32
        self._btn_h   = 22
        self._btn_pad = 8
        self._update_btn_rect()

    # ------------------------------------------------------------------ helpers

    def _update_btn_rect(self):
        """Prepočíta pozíciu tlačidla podľa aktuálnej veľkosti okna."""
        sw, sh = self.screen.get_size()
        self._btn_rect = pygame.Rect(
            sw - self._btn_w - self._btn_pad,
            sh - self._btn_h - self._btn_pad,
            self._btn_w,
            self._btn_h,
        )

    def _draw_overlay(self):
        """Vykreslí HUD vrstvu priamo na screen (nad všetkými stavmi)."""
        r = self._btn_rect

        # Polopriesvitné pozadie tlačidla
        s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        hover = r.collidepoint(pygame.mouse.get_pos())
        bg_alpha = 200 if hover else 130
        pygame.draw.rect(s, (30, 30, 40, bg_alpha), s.get_rect(), border_radius=5)
        border_color = (200, 200, 220, 220) if hover else (120, 120, 140, 160)
        pygame.draw.rect(s, border_color, s.get_rect(), width=1, border_radius=5)
        self.screen.blit(s, r.topleft)

        # Ikona – rohové šípky (štýl fullscreen symbolu)
        ic  = r.inflate(-8, -6)
        c   = (220, 220, 230)
        sz  = 4
        lw  = 1
        corners = [
            (ic.left,  ic.top,    +1, +1),
            (ic.right, ic.top,    -1, +1),
            (ic.left,  ic.bottom, +1, -1),
            (ic.right, ic.bottom, -1, -1),
        ]
        for cx2, cy2, dx, dy in corners:
            pygame.draw.line(self.screen, c, (cx2, cy2), (cx2 + dx * sz, cy2), lw)
            pygame.draw.line(self.screen, c, (cx2, cy2), (cx2, cy2 + dy * sz), lw)

        # "F11" hint naľavo od tlačidla
        hint = self._hud_font.render("F11", True, (120, 120, 135))
        self.screen.blit(
            hint,
            (r.left - hint.get_width() - 4, r.top + (r.height - hint.get_height()) // 2)
        )

    # ------------------------------------------------------------------ fullscreen

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                pygame.FULLSCREEN,
            )
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
            )
        self._update_btn_rect()

    # ------------------------------------------------------------------ loop

    def run(self):
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            clock.tick(60)
            self.get_events()
            self.update()
            self.render()

    def update(self):
        self.state_stack[-1].update()

    def render(self):
        self.state_stack[-1].render(self.game_canvas)

        screen_w, screen_h = self.screen.get_size()
        canvas_w, canvas_h = self.game_canvas.get_size()
        offset_x = (screen_w - canvas_w) // 2
        offset_y = (screen_h - canvas_h) // 2

        self.screen.fill((0, 0, 0))
        self.screen.blit(self.game_canvas, (offset_x, offset_y))

        # HUD overlay vždy navrchu
        self._draw_overlay()

        pygame.display.flip()

    def load_states(self):
        self.state_manager.change_state("MainMenu")

    def get_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                self.running = False

            # F11 klávesa
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()

            # Klik na fullscreen tlačidlo
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._btn_rect.collidepoint(event.pos):
                    self.toggle_fullscreen()

            if self.state_stack:
                self.state_stack[-1].handle_events(event)

    def draw_text(self, screen: pygame.Surface, text: str, color: pygame.Color | tuple, x: int, y: int):
        text_surface = self.h1_font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        screen.blit(text_surface, text_rect)


if __name__ == '__main__':
    app = BomberManApp()
    app.run()
    pygame.quit()