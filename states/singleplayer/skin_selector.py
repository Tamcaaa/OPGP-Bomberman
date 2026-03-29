import pygame, os
from states.general.state import State
import config
from managers.state_manager import StateManager
from managers.music_manager import MusicManager

# Akcenty hráčov
ACCENT = {
    1: (124, 106, 247),   # violet
    2: (249, 115, 22),    # orange
}
ACCENT_DIM = {
    1: (124, 106, 247, 30),
    2: (249, 115, 22, 30),
}

# --- Dostupné farby ---
AVAILABLE_COLORS = {
    config.WHITE_PLAYER:       "White",
    config.BLACK_PLAYER:       "Black",
    config.RED_PLAYER:         "Red",
    config.BLUE_PLAYER:        "Blue",
    config.DARK_GREEN_PLAYER:  "Green",
    config.LIGHT_GREEN_PLAYER: "Green",
    config.YELLOW_PLAYER:      "Yellow",
    config.PINK_PLAYER:        "Pink",
    config.ORANGE_PLAYER:      "Orange",
    config.PURPLE_PLAYER:      "Purple",
    config.BROWN_PLAYER:       "Brown",
    config.CYAN_PLAYER:        "Cyan",
}


class SkinSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Skin Selection")
        self.state_manager = StateManager(self.game)

        # Pozadie (stále načítame, ale len ako fallback – kreslíme cez config.BG_BASE)
        try:
            self.bg = pygame.image.load(
                os.path.join(game.photos_dir, "skinselector_bg.png")
            ).convert()
        except Exception:
            self.bg = None

        # Sprite hráča (idle animácia) – zachovaná presne ako bola
        self.idle_frames = []
        for i in range(3):
            frame = pygame.image.load(
                os.path.join(game.photos_dir, "player_animations", f"p_1_idle_{i}.png")
            ).convert_alpha()
            w, h = frame.get_size()
            frame = pygame.transform.scale(frame, (w * 3, h * 3))
            self.idle_frames.append(frame)
        self.idle_index = 0
        self.last_idle_update = pygame.time.get_ticks()
        self.idle_fps = 4

        # Čiapky
        self.hat_images = {}
        self.hat_thumbs = {}
        for hat in config.HATS:
            name = hat["name"]
            file = hat["file"]
            if file is None:
                self.hat_images[name] = None
                self.hat_thumbs[name] = None
                continue
            path = os.path.join(game.photos_dir, "../assets/player_hats", file)
            if not os.path.exists(path):
                print("Missing hat image:", path)
                self.hat_images[name] = None
                self.hat_thumbs[name] = None
                continue
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (48,48))
            self.hat_images[name] = img
            tw = 36
            scale = tw / max(img.get_width(), img.get_height())
            thumb = pygame.transform.smoothscale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale))
            )
            self.hat_thumbs[name] = thumb

        # Stav výberu
        self.players = {
            1: {"color": None, "hat": None},
            2: {"color": None, "hat": None},
        }
        self.selected_index = {
            1: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
            2: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
        }
        self.active_tab = {1: config.TAB_COLORS, 2: config.TAB_COLORS}
        self.scroll_top = {
            1: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
            2: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
        }

        # Fonty – zachovaný CaveatBrush
        self.font_lg   = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_md   = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.font_sm   = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
        self.font_xs   = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        # Layout
        PANEL_W = 340
        PANEL_H = 480
        top_y   = 55

        self.panel_rects = {
            1: pygame.Rect(30,                          top_y, PANEL_W, PANEL_H),
            2: pygame.Rect(config.SCREEN_WIDTH - 30 - PANEL_W, top_y, PANEL_W, PANEL_H),
        }

        # Výška zón vo vnútri panelu (zhora):
        #   [preview_zone]  130 px
        #   [tab_bar]        36 px  (s 8px medzere nad/pod)
        #   [list_area]      zvyšok – 48px pre hint + button
        self.PREVIEW_H   = 130
        self.TAB_H       = 36
        self.TAB_PAD     = 8       # medzera nad tabbar
        self.LIST_PAD    = 8       # medzera pod tabbar
        self.HINT_H      = 48
        self.PANEL_PAD   = 14
        self.ROW_H       = 42
        self.CHIP_R      = 12

        # Ovládanie (nezmenené)
        self.controls = {
            1: {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a,
                'right': pygame.K_d, 'select': pygame.K_LSHIFT},
            2: {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT, 'select': pygame.K_RETURN},
        }

    # ------------------------------------------------------------------ helpers
    def _preview_rect(self, panel: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(panel.x, panel.y, panel.width, self.PREVIEW_H)

    def _tabbar_rect(self, panel: pygame.Rect) -> pygame.Rect:
        y = panel.y + self.PREVIEW_H + self.TAB_PAD
        return pygame.Rect(
            panel.x + self.PANEL_PAD, y,
            panel.width - 2 * self.PANEL_PAD, self.TAB_H
        )

    def _list_rect(self, panel: pygame.Rect) -> pygame.Rect:
        tab = self._tabbar_rect(panel)
        y   = tab.bottom + self.LIST_PAD
        h   = panel.bottom - y - self.HINT_H
        return pygame.Rect(panel.x + self.PANEL_PAD, y,
                           panel.width - 2 * self.PANEL_PAD, max(40, h))

    def _visible_count(self, panel: pygame.Rect) -> int:
        return max(1, self._list_rect(panel).height // self.ROW_H)

    def _clamp_scroll(self, pid, tab, total, panel):
        vis = self._visible_count(panel)
        sel = self.selected_index[pid][tab]
        top = self.scroll_top[pid][tab]
        if sel < top:
            top = sel
        elif sel >= top + vis:
            top = sel - vis + 1
        self.scroll_top[pid][tab] = max(0, min(max(0, total - vis), top))

    # ------------------------------------------------------------------ player color (živý výber)
    def _player_color(self, player_id: int) -> tuple:
        """Vráti aktuálne vybranú farbu hráča podľa kurzora v zozname (živо pri scrollovaní)."""
        color_keys = list(AVAILABLE_COLORS.keys())
        idx = self.selected_index[player_id][config.TAB_COLORS]
        return color_keys[idx]

    # ------------------------------------------------------------------ drawing primitives
    def _draw_rrect(self, surf, color, rect, radius=14, alpha=255, border=0, border_color=None):
        """Vykreslí rounded rect, voliteľne s alpha a border."""
        if alpha < 255:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color[:3], alpha), s.get_rect(), border_radius=radius)
            if border and border_color:
                pygame.draw.rect(s, (*border_color[:3], alpha),
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
        # jemný tieň
        shadow = font.render(text, True, (0, 0, 0))
        surf.blit(shadow, (x + 1, y + 1))
        surf.blit(rendered, (x, y))

    # ------------------------------------------------------------------ panel shell
    def draw_panel(self, screen, panel: pygame.Rect, player_id: int):
        acc = self._player_color(player_id)
        is_ready = self.players[player_id]["color"] is not None

        # Základný panel – oramovanie vždy v živej farbe hráča
        self._draw_rrect(screen, config.BG_PANEL, panel, radius=18, alpha=220,
                         border=1, border_color=acc)

        # Jemný vrchný glow vždy (intenzívnejší ak ready)
        glow_alpha = 100 if is_ready else 40
        glow = pygame.Surface((panel.width, 6), pygame.SRCALPHA)
        for gx in range(panel.width):
            a = int(glow_alpha * (1 - abs(gx - panel.width / 2) / (panel.width / 2)))
            pygame.draw.line(glow, (*acc, a), (gx, 0), (gx, 5))
        screen.blit(glow, (panel.x, panel.y))

    # ------------------------------------------------------------------ preview zone
    def draw_player_preview(self, screen, player_id: int, panel: pygame.Rect):
        color_keys = list(AVAILABLE_COLORS.keys())
        chosen_color = color_keys[self.selected_index[player_id][config.TAB_COLORS]]

        # Animovaný frame
        num_frames = len(self.idle_frames)
        frame_index = (pygame.time.get_ticks() // (1000 // self.idle_fps)) % num_frames
        frame = self.idle_frames[frame_index]

        img = self.tint_image(frame, chosen_color)
        if player_id == 2:
            img = pygame.transform.flip(img, True, False)

        prev_rect = self._preview_rect(panel)

        # Tintovaný kruh za hráčom – v živej farbe hráča
        circle_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(circle_surf, (*chosen_color, 35), (45, 45), 45)
        cx = prev_rect.centerx - 45
        cy = prev_rect.y + prev_rect.height - 90 - 10
        screen.blit(circle_surf, (cx, cy))

        # Hráč
        pw = img.get_width()
        ph = img.get_height()
        px = prev_rect.centerx - pw // 2
        py = prev_rect.y + prev_rect.height - ph - 10
        screen.blit(img, (px, py))

        # Čiapka
        hat_def  = config.HATS[self.selected_index[player_id][config.TAB_HATS]]
        hat_name = hat_def["name"]
        if hat_name != "None":
            hat_img = self.hat_images.get(hat_name)
            if hat_img:
                ox, oy = hat_def["offset"]
                if hat_name == "Devil":
                    if not hasattr(self, 'preview_corner_offset'):
                        self.preview_corner_offset = {1: 10, 2: -10}
                    ox += self.preview_corner_offset.get(player_id, 0)
                HAT_IDLE_OFFSETS = [0, -4, 0]
                hat_offset = HAT_IDLE_OFFSETS[frame_index]
                if player_id == 2:
                    hat_img = pygame.transform.flip(hat_img, True, False)
                screen.blit(hat_img, (px + ox, py + oy + hat_offset))

        # Meno / "PLAYER X" label
        label = f"PLAYER {player_id}"
        self._text(screen, label, self.font_xs, chosen_color,
                   (prev_rect.centerx, prev_rect.y + 8), align="center")

        # "Ready!" badge
        if self.players[player_id]["color"]:
            badge_text = "READY"
            bw = self.font_xs.size(badge_text)[0] + 16
            bh = 20
            bx = prev_rect.centerx - bw // 2
            by = prev_rect.y + 26
            self._draw_rrect(screen, chosen_color, pygame.Rect(bx, by, bw, bh),
                             radius=10, alpha=30)
            border_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(border_s, (*chosen_color, 120), border_s.get_rect(),
                             width=1, border_radius=10)
            screen.blit(border_s, (bx, by))
            self._text(screen, badge_text, self.font_xs, chosen_color,
                       (prev_rect.centerx, by + 3), align="center")

    # ------------------------------------------------------------------ tab bar
    def draw_tab_bar(self, screen, panel: pygame.Rect, player_id: int):
        tab_rect = self._tabbar_rect(panel)
        acc = self._player_color(player_id)

        # Pozadie tab baru
        self._draw_rrect(screen, config.BG_TAB_BAR, tab_rect, radius=10, alpha=200,
                         border=1, border_color=config.BORDER_SUBTLE)

        half = (tab_rect.width - 4) // 2
        tabs = [
            pygame.Rect(tab_rect.x + 2, tab_rect.y + 2, half, tab_rect.height - 4),
            pygame.Rect(tab_rect.x + half + 2, tab_rect.y + 2, half, tab_rect.height - 4),
        ]
        active = self.active_tab[player_id]
        for i, tr in enumerate(tabs):
            if i == active:
                self._draw_rrect(screen, config.BG_TAB_ACTIVE, tr, radius=8, alpha=255)
                # farebná čiarka dole
                line_surf = pygame.Surface((tr.width - 16, 2), pygame.SRCALPHA)
                line_surf.fill((*acc, 200))
                screen.blit(line_surf, (tr.x + 8, tr.bottom - 4))
            label = config.TAB_NAMES[i]
            color = config.TEXT_PRIMARY if i == active else config.TEXT_MUTED
            self._text(screen, label, self.font_sm, color,
                       (tr.centerx, tr.y + 8), align="center")

    # ------------------------------------------------------------------ color list
    def draw_colors_list(self, screen, player_id: int, panel: pygame.Rect):
        area = self._list_rect(panel)
        acc  = self._player_color(player_id)
        color_keys = list(AVAILABLE_COLORS.keys())
        total = len(color_keys)
        vis   = self._visible_count(panel)
        top   = self.scroll_top[player_id][config.TAB_COLORS]

        self._draw_rrect(screen, config.BG_LIST, area, radius=12, alpha=220)

        prev_clip = screen.get_clip()
        screen.set_clip(area)

        for i in range(vis):
            idx = top + i
            if idx >= total:
                break
            row_y = area.y + i * self.ROW_H
            row_rect = pygame.Rect(area.x, row_y, area.width, self.ROW_H)

            selected = self.selected_index[player_id][config.TAB_COLORS] == idx
            taken    = (self.players[2 if player_id == 1 else 1]["color"] == color_keys[idx])

            if selected:
                self._draw_rrect(screen, config.BG_ITEM_SEL, row_rect, radius=8, alpha=255)
                # accent rail vľavo
                rail = pygame.Surface((3, self.ROW_H - 10), pygame.SRCALPHA)
                rail.fill((*acc, 220))
                screen.blit(rail, (area.x + 2, row_y + 5))

            # Color chip
            chip_x = area.x + 18
            chip_y = row_y + self.ROW_H // 2
            r, g, b = color_keys[idx]
            if taken:
                r, g, b = int(r * 0.3), int(g * 0.3), int(b * 0.3)
            pygame.draw.circle(screen, (r, g, b), (chip_x, chip_y), self.CHIP_R)
            if selected:
                pygame.draw.circle(screen, acc, (chip_x, chip_y), self.CHIP_R + 4, 2)
            elif not taken:
                pygame.draw.circle(screen, config.BORDER_FOCUS, (chip_x, chip_y), self.CHIP_R + 1, 1)

            # Meno farby
            name = AVAILABLE_COLORS[color_keys[idx]]
            col  = config.TEXT_MUTED if taken else (config.TEXT_PRIMARY if selected else (160, 165, 200))
            self._text(screen, name, self.font_md, col, (chip_x + 26, row_y + 9))

            # Checkmark ak selected
            if selected:
                self._text(screen, "\u2022", self.font_sm, acc, (area.right - 22, row_y + 10))

        screen.set_clip(prev_clip)
        self._draw_scrollbar(screen, area, top, vis, total, acc)

    # ------------------------------------------------------------------ hats list
    def draw_hats_list(self, screen, player_id: int, panel: pygame.Rect):
        area = self._list_rect(panel)
        acc  = self._player_color(player_id)
        total = len(config.HATS)
        vis   = self._visible_count(panel)
        top   = self.scroll_top[player_id][config.TAB_HATS]

        self._draw_rrect(screen, config.BG_LIST, area, radius=12, alpha=220)

        prev_clip = screen.get_clip()
        screen.set_clip(area)

        for i in range(vis):
            idx = top + i
            if idx >= total:
                break
            hat = config.HATS[idx]
            row_y    = area.y + i * self.ROW_H
            row_rect = pygame.Rect(area.x, row_y, area.width, self.ROW_H)
            selected = self.selected_index[player_id][config.TAB_HATS] == idx

            if selected:
                self._draw_rrect(screen, config.BG_ITEM_SEL, row_rect, radius=8, alpha=255)
                rail = pygame.Surface((3, self.ROW_H - 10), pygame.SRCALPHA)
                rail.fill((*acc, 220))
                screen.blit(rail, (area.x + 2, row_y + 5))

            # Thumbnail
            thumb = self.hat_thumbs.get(hat["name"])
            tx = area.x + 10
            ty = row_y + (self.ROW_H - 36) // 2
            if thumb is not None:
                screen.blit(thumb, (tx, ty))
            else:
                # "None" placeholder
                placeholder = pygame.Surface((36, 36), pygame.SRCALPHA)
                pygame.draw.rect(placeholder, (*config.BORDER_SUBTLE, 120), placeholder.get_rect(), border_radius=6)
                pygame.draw.line(placeholder, (*config.TEXT_MUTED, 150), (8, 28), (28, 8), 2)
                screen.blit(placeholder, (tx, ty))

            # Meno
            col = config.TEXT_PRIMARY if selected else (160, 165, 200)
            self._text(screen, hat["name"], self.font_md, col, (tx + 44, row_y + 10))

            if selected:
                self._text(screen, "\u2022", self.font_sm, acc, (area.right - 22, row_y + 10))

        screen.set_clip(prev_clip)
        self._draw_scrollbar(screen, area, top, vis, total, acc)

    # ------------------------------------------------------------------ scrollbar
    def _draw_scrollbar(self, screen, area, top, vis, total, accent):
        if total <= vis:
            return
        bar_w = 4
        x     = area.right - bar_w - 3
        track = pygame.Rect(x, area.y + 6, bar_w, area.height - 12)
        pygame.draw.rect(screen, config.SCROLLBAR_TRK, track, border_radius=2)
        knob_h  = max(16, int(track.height * (vis / total)))
        max_top = total - vis
        knob_y  = track.y + int((top / max_top) * (track.height - knob_h)) if max_top else track.y
        knob    = pygame.Rect(x, knob_y, bar_w, knob_h)
        pygame.draw.rect(screen, accent, knob, border_radius=2)

    # ------------------------------------------------------------------ hint bar
    def draw_hint_bar(self, screen, panel: pygame.Rect, player_id: int):
        y = panel.bottom - self.HINT_H + 6
        acc = self._player_color(player_id)

        if player_id == 1:
            nav_hint    = "A/D  tab    W/S  scroll"
            select_hint = "Shift  =  lock in"
        else:
            nav_hint    = "LEFT/RIGHT  tab    UP/DOWN  scroll"
            select_hint = "Enter  =  lock in"

        self._text(screen, nav_hint, self.font_xs, config.TEXT_HINT,
                   (panel.centerx, y), align="center")
        self._text(screen, select_hint, self.font_xs, (*acc,),
                   (panel.centerx, y + 18), align="center")

    # ------------------------------------------------------------------ tint
    def tint_image(self, image, color):
        tinted = image.copy()
        tint   = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))
        tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        return tinted

    # ------------------------------------------------------------------ animation tick
    def update_idle_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 1000 // self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

    # ------------------------------------------------------------------ main draw
    def draw(self, screen):
        self.update_idle_animation()

        # Pozadie
        screen.fill(config.BG_BASE)
        if self.bg:
            bg_scaled = pygame.transform.scale(self.bg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            dark = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            dark.fill((10, 12, 18, 180))
            screen.blit(bg_scaled, (0, 0))
            screen.blit(dark, (0, 0))

        # Title
        self._text(screen, "BOMBERMAN", self.font_lg, config.TEXT_PRIMARY,
           (config.SCREEN_WIDTH // 2, 10), align="center")

        # "Choose your skin" podnadpis
        self._text(screen, "CHOOSE YOUR SKIN", self.font_md, config.TEXT_MUTED,
                   (config.SCREEN_WIDTH // 2, 38), align="center")

        for pid in (1, 2):
            panel = self.panel_rects[pid]

            # Panel shell
            self.draw_panel(screen, panel, pid)

            # Preview s animáciou
            self.draw_player_preview(screen, pid, panel)

            # Oddeľovač preview / list
            sep_y = panel.y + self.PREVIEW_H
            sep_s = pygame.Surface((panel.width - 2 * self.PANEL_PAD, 1), pygame.SRCALPHA)
            sep_s.fill((*config.BORDER_SUBTLE, 180))
            screen.blit(sep_s, (panel.x + self.PANEL_PAD, sep_y))

            # Tab bar
            self.draw_tab_bar(screen, panel, pid)

            # Zoznam
            if self.active_tab[pid] == config.TAB_COLORS:
                self.draw_colors_list(screen, pid, panel)
            else:
                self.draw_hats_list(screen, pid, panel)

            # Hint
            self.draw_hint_bar(screen, panel, pid)

        # "SPACE to continue" – uprostred dole, len ak obaja ready
        if self.players[1]["color"] and self.players[2]["color"]:
            msg = "SPACE  –  LET'S PLAY"
            bw  = self.font_md.size(msg)[0] + 40
            bh  = 38
            bx  = config.SCREEN_WIDTH // 2 - bw // 2
            by  = self.panel_rects[1].bottom + 14

            # žltý button
            BTN_COLOR = (247, 201, 72)
            self._draw_rrect(screen, BTN_COLOR, pygame.Rect(bx, by, bw, bh), radius=12)
            self._text(screen, msg, self.font_md, config.BG_BASE, (config.SCREEN_WIDTH // 2, by + 8),
                       align="center")

    # ------------------------------------------------------------------ events (nezmenené)
    def handle_events(self, event):
        color_keys = list(AVAILABLE_COLORS.keys())
        if event.type != pygame.KEYDOWN:
            return

        def total_count(tab):
            return len(color_keys) if tab == config.TAB_COLORS else len(config.HATS)

        # Player 1
        if event.key == self.controls[1]['left']:
            self.active_tab[1] = max(0, self.active_tab[1] - 1)
        elif event.key == self.controls[1]['right']:
            self.active_tab[1] = min(len(config.TAB_NAMES) - 1, self.active_tab[1] + 1)
        elif event.key == self.controls[1]['up']:
            tab = self.active_tab[1]
            t = total_count(tab)
            self.selected_index[1][tab] = (self.selected_index[1][tab] - 1) % t
            self._clamp_scroll(1, tab, t, self.panel_rects[1])
        elif event.key == self.controls[1]['down']:
            tab = self.active_tab[1]
            t = total_count(tab)
            self.selected_index[1][tab] = (self.selected_index[1][tab] + 1) % t
            self._clamp_scroll(1, tab, t, self.panel_rects[1])
        elif event.key == self.controls[1]['select']:
            color_idx = self.selected_index[1][config.TAB_COLORS]
            chosen_color = color_keys[color_idx]
            if chosen_color != self.players[2]["color"]:
                self.players[1]["color"] = chosen_color
            hat_idx = self.selected_index[1][config.TAB_HATS]
            self.players[1]["hat"] = config.HATS[hat_idx]["name"]

        # Player 2
        if event.key == self.controls[2]['left']:
            self.active_tab[2] = max(0, self.active_tab[2] - 1)
        elif event.key == self.controls[2]['right']:
            self.active_tab[2] = min(len(config.TAB_NAMES) - 1, self.active_tab[2] + 1)
        elif event.key == self.controls[2]['up']:
            tab = self.active_tab[2]
            t = total_count(tab)
            self.selected_index[2][tab] = (self.selected_index[2][tab] - 1) % t
            self._clamp_scroll(2, tab, t, self.panel_rects[2])
        elif event.key == self.controls[2]['down']:
            tab = self.active_tab[2]
            t = total_count(tab)
            self.selected_index[2][tab] = (self.selected_index[2][tab] + 1) % t
            self._clamp_scroll(2, tab, t, self.panel_rects[2])
        elif event.key == self.controls[2]['select']:
            color_idx = self.selected_index[2][config.TAB_COLORS]
            chosen_color = color_keys[color_idx]
            if chosen_color != self.players[1]["color"]:
                self.players[2]["color"] = chosen_color
            hat_idx = self.selected_index[2][config.TAB_HATS]
            self.players[2]["hat"] = config.HATS[hat_idx]["name"]

        # Pokračovanie
        if event.key == pygame.K_SPACE and self.players[1]["color"] and self.players[2]["color"]:
            payload = {
                1: (self.players[1]["color"], self.players[1]["hat"]),
                2: (self.players[2]["color"], self.players[2]["hat"]),
            }
            self.state_manager.change_state("MapSelector", payload)

    def render(self, screen):
        self.draw(screen)
