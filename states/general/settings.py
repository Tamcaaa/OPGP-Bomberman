import pygame
import config
import os
from states.general.state import State
from custom_classes.button import Button

class Settings(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Settings")

        self.volume     = game.settings.get("volume", 0.5)
        self.last_volume = self.volume if self.volume > 0.0 else 0.5

        # Fonty
        self.font_lg = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_md = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.font_sm = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
        self.font_xs = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        # Pozadie
        try:
            self.background_image = pygame.transform.scale(
                pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(),
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )
        except Exception:
            self.background_image = None

        # Zvukové ikony
        self.sound_on_img  = pygame.transform.scale(
            pygame.image.load("assets/not_muted.png").convert_alpha(), (20, 20))
        self.sound_off_img = pygame.transform.scale(
            pygame.image.load("assets/mute.png").convert_alpha(), (20, 20))

        # Key bindings
        self.key_bindings = {
            "player1": list(config.PLAYER1_MOVE_KEYS),
            "player2": list(config.PLAYER2_MOVE_KEYS)
        }
        self.editing_key    = None
        self.editing_player = None
        self.editing_action = None

        # Layout – dva panely vedľa seba
        cx        = config.SCREEN_WIDTH // 2
        panel_w   = 280
        panel_h   = 340
        panel_gap = 20
        panel_y   = 80

        self.panel_left  = pygame.Rect(cx - panel_w - panel_gap // 2, panel_y, panel_w, panel_h)
        self.panel_right = pygame.Rect(cx + panel_gap // 2,            panel_y, panel_w, panel_h)

        # Volume slider
        self.slider_x      = self.panel_left.x + 20
        self.slider_y      = self.panel_left.y + 120
        self.slider_width  = panel_w - 40
        self.slider_height = 6
        self.slider_handle_radius = 8

        # Mute button (IconButton)
        mute_x = self.panel_left.x + 20
        mute_y = self.slider_y + 30
        current_img = self.sound_on_img if self.volume > 0.0 else self.sound_off_img
        self.mute_button = IconButton(mute_x, mute_y, 32, 32, current_img)

        # Back button
        self.back_button = Button(
            cx - 80, config.SCREEN_HEIGHT - 68, 160, 44, "Back",
            font="CaveatBrush-Regular.ttf", style="outline"
        )

        # Key binding buttons
        self.key_bind_buttons = {}
        actions   = ["Up", "Left", "Down", "Right", "Bomb"]
        btn_w     = panel_w - 32
        btn_h     = 36
        gap       = 10
        start_y_p = self.panel_left.y + 44

        for i, action in enumerate(actions):
            y = start_y_p + i * (btn_h + gap)

            btn_p1 = Button(
                self.panel_left.x + 16, y, btn_w, btn_h,
                f"{action}:  {pygame.key.name(self.key_bindings['player1'][i])}",
                font="CaveatBrush-Regular.ttf", font_size=16, style="outline"
            )
            self.key_bind_buttons[f"player1_{i}"] = btn_p1

            btn_p2 = Button(
                self.panel_right.x + 16, y, btn_w, btn_h,
                f"{action}:  {pygame.key.name(self.key_bindings['player2'][i])}",
                font="CaveatBrush-Regular.ttf", font_size=16, style="outline"
            )
            self.key_bind_buttons[f"player2_{i}"] = btn_p2

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
        if self.editing_key is not None:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    self.key_bindings[self.editing_player][self.editing_action] = event.key
                    btn_key     = f"{self.editing_player}_{self.editing_action}"
                    action_name = ["Up", "Left", "Down", "Right", "Bomb"][self.editing_action]
                    self.key_bind_buttons[btn_key].text = (
                        f"{action_name}:  {pygame.key.name(event.key)}"
                    )
                    self.update_player_config()
                self.editing_key    = None
                self.editing_player = None
                self.editing_action = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked():
                self.exit_state()
            elif self.mute_button.is_clicked():
                self.toggle_mute()
            else:
                mx, my = pygame.mouse.get_pos()
                slider_rect = pygame.Rect(
                    self.slider_x, self.slider_y - 8,
                    self.slider_width, self.slider_height + 16
                )
                if slider_rect.collidepoint(mx, my):
                    self.set_volume_from_slider(mx)
                else:
                    for btn_key, button in self.key_bind_buttons.items():
                        if button.is_clicked():
                            parts = btn_key.split("_")
                            self.editing_player = parts[0]
                            self.editing_action = int(parts[1])
                            self.editing_key    = btn_key
                            button.text = "Press any key..."
                            break

        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                mx, _ = pygame.mouse.get_pos()
                if self.slider_x <= mx <= self.slider_x + self.slider_width:
                    self.set_volume_from_slider(mx)

    def set_volume_from_slider(self, mouse_x):
        rel_x        = mouse_x - self.slider_x
        self.volume  = max(0.0, min(1.0, rel_x / self.slider_width))
        if self.volume > 0.0:
            self.last_volume       = self.volume
            self.mute_button.image = self.sound_on_img
        else:
            self.mute_button.image = self.sound_off_img
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def toggle_mute(self):
        if self.volume > 0.0:
            self.last_volume       = self.volume
            self.volume            = 0.0
            self.mute_button.image = self.sound_off_img
        else:
            self.volume            = self.last_volume
            self.mute_button.image = self.sound_on_img
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def update_player_config(self):
        config.PLAYER1_MOVE_KEYS[:]          = self.key_bindings["player1"]
        config.PLAYER2_MOVE_KEYS[:]          = self.key_bindings["player2"]
        config.PLAYER_CONFIG[1]['move_keys'] = config.PLAYER1_MOVE_KEYS
        config.PLAYER_CONFIG[2]['move_keys'] = config.PLAYER2_MOVE_KEYS

    # ------------------------------------------------------------------ render
    def render(self, screen):
        # Pozadie
        screen.fill(config.BG_BASE)
        if self.background_image:
            dark = pygame.Surface(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            dark.fill((10, 12, 18, 180))
            screen.blit(self.background_image, (0, 0))
            screen.blit(dark, (0, 0))

        cx = config.SCREEN_WIDTH // 2

        # Nadpis
        self._text(screen, "SETTINGS", self.font_lg, config.TEXT_PRIMARY,
                   (cx, 18), align="center")
        self._text(screen, "KEY BINDINGS  &  AUDIO", self.font_xs, config.TEXT_MUTED,
                   (cx, 46), align="center")

        # ---- Ľavý panel – Key Bindings P1 ----
        self._draw_rrect(screen, config.BG_PANEL, self.panel_left, radius=16, alpha=220,
                         border=1, border_color=config.BORDER_SUBTLE)
        self._glow_line(screen, self.panel_left, config.BTN_BEIGE, alpha=50)
        self._text(screen, "PLAYER 1", self.font_sm, config.BTN_BEIGE,
                   (self.panel_left.centerx, self.panel_left.y + 14), align="center")

        # ---- Pravý panel – Key Bindings P2 ----
        self._draw_rrect(screen, config.BG_PANEL, self.panel_right, radius=16, alpha=220,
                         border=1, border_color=config.BORDER_SUBTLE)
        self._glow_line(screen, self.panel_right, config.BTN_BEIGE, alpha=50)
        self._text(screen, "PLAYER 2", self.font_sm, config.BTN_BEIGE,
                   (self.panel_right.centerx, self.panel_right.y + 14), align="center")

        # Key bind buttons
        for button in self.key_bind_buttons.values():
            button.draw(screen)

        # ---- Volume panel (pod ľavým) ----
        vol_panel = pygame.Rect(
            self.panel_left.x,
            self.panel_left.bottom + 16,
            self.panel_left.width * 2 + 20,
            90
        )
        self._draw_rrect(screen, config.BG_PANEL, vol_panel, radius=14, alpha=220,
                         border=1, border_color=config.BORDER_SUBTLE)

        # Volume label
        self._text(screen, f"VOLUME  {int(self.volume * 100)}%", self.font_sm, config.TEXT_PRIMARY,
                   (vol_panel.x + 20, vol_panel.y + 14))

        # Slider track
        sy = vol_panel.y + 50
        sx = vol_panel.x + 20
        sw = vol_panel.width - 60
        self.slider_x     = sx
        self.slider_y     = sy
        self.slider_width = sw

        pygame.draw.rect(screen, config.SLIDER_TRACK,
                         (sx, sy, sw, self.slider_height), border_radius=3)
        filled = int(self.volume * sw)
        if filled > 0:
            pygame.draw.rect(screen, config.SLIDER_FILL,
                             (sx, sy, filled, self.slider_height), border_radius=3)
        # Handle
        hx = sx + filled
        hy = sy + self.slider_height // 2
        pygame.draw.circle(screen, config.BTN_BEIGE, (hx, hy), self.slider_handle_radius)
        pygame.draw.circle(screen, config.BG_BASE,   (hx, hy), self.slider_handle_radius - 3)

        # Mute button
        self.mute_button.rect.x = sx + sw + 4
        self.mute_button.rect.y = sy - 14
        self.mute_button.draw(screen)

        # Editing hint
        if self.editing_key is not None:
            action_names = ["Up", "Left", "Down", "Right", "Bomb"]
            p_num = "1" if self.editing_player == "player1" else "2"
            hint  = f"Press key for P{p_num} {action_names[self.editing_action]}  (ESC = cancel)"
            self._text(screen, hint, self.font_sm, config.BTN_BEIGE,
                       (cx, config.SCREEN_HEIGHT - 90), align="center")

        # Back button
        self.back_button.rect.x = vol_panel.left - 180
        self.back_button.draw(screen)


# ------------------------------------------------------------------ IconButton
class IconButton:
    def __init__(self, x, y, width, height, image):
        self.rect  = pygame.Rect(x, y, width, height)
        self.image = image

    def draw(self, screen):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        bg = (40, 44, 65) if hovered else (26, 30, 46)
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        pygame.draw.rect(screen, (50, 55, 85), self.rect, width=1, border_radius=8)
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect)

    def is_clicked(self):
        return (self.rect.collidepoint(pygame.mouse.get_pos())
                and pygame.mouse.get_pressed()[0])
