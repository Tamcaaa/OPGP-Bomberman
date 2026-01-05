import pygame, os
from states.state import State
import config
from managers.state_manager import StateManager

# --- Dostupné farby ---
AVAILABLE_COLORS = {
    config.WHITE_PLAYER: "White",
    config.BLACK_PLAYER: "Black",
    config.RED_PLAYER: "Red",
    config.BLUE_PLAYER: "Blue",
    config.DARK_GREEN_PLAYER: "Green",
    config.LIGHT_GREEN_PLAYER: "Green",
    config.YELLOW_PLAYER: "Yellow",
    config.PINK_PLAYER: "Pink",
    config.ORANGE_PLAYER: "Orange",
    config.PURPLE_PLAYER: "Purple",
    config.BROWN_PLAYER: "Brown",
    config.CYAN_PLAYER: "Cyan"
}

class SkinSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Skin Selection")
        self.state_manager = StateManager(self.game)

        # Pozadie
        self.bg = pygame.image.load(os.path.join(game.photos_dir, "skinselector_bg.png")).convert()
        self.title_img = pygame.image.load(os.path.join(game.photos_dir, "skin_selector_txt.png"))

        # Sprite hráča (idle)
        self.idle_frames = []
        for i in range(3):
            frame = pygame.image.load(
                os.path.join(game.photos_dir, "player_color", f"p_1_idle_{i}.png")
            ).convert_alpha()
            w, h = frame.get_size()
            frame = pygame.transform.scale(frame, (w * 8, h * 8))
            self.idle_frames.append(frame)
        self.idle_index = 0
        self.last_idle_update = pygame.time.get_ticks()
        self.idle_fps = 4

        # Načítanie čiapok (thumbnails aj plná vrstva)
        self.hat_images = {}
        self.hat_thumbs = {}

        for hat in config.HATS:
            name = hat["name"]
            file = hat["file"]

            # None = žiadna čiapka, nič nenačítavame
            if file is None:
                self.hat_images[name] = None
                self.hat_thumbs[name] = None
                continue

            path = os.path.join(game.photos_dir, "../assets/player_hats", file)

            if not os.path.exists(path):
                print("❌ Missing hat image:", path)
                self.hat_images[name] = None
                self.hat_thumbs[name] = None
                continue

            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (100, 100))

            self.hat_images[name] = img

            # thumbnail (~40px)
            tw = 40
            scale = tw / max(img.get_width(), img.get_height())
            thumb = pygame.transform.smoothscale(
                img,
                (int(img.get_width() * scale), int(img.get_height() * scale))
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

        # Scroll okná (prvý viditeľný index) – zvlášť pre hráča a tabu
        self.scroll_top = {
            1: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
            2: {config.TAB_COLORS: 0, config.TAB_HATS: 0},
        }

        # Fonty
        self.font = pygame.font.Font("CaveatBrush-Regular.ttf", 28)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.small_font = pygame.font.Font("CaveatBrush-Regular.ttf", 20)

        # Panely
        self.panel_rects = {
            1: pygame.Rect(40, 70, 360, 400),
            2: pygame.Rect(config.SCREEN_WIDTH - 400, 70, 360, 400),
        }
        self.panel_pad = 20
        self.row_spacing = 46     # výška jedného riadku
        self.list_left_pad = 24   # kde sa kreslí chip/thumbnail
        self.tab_height = 34      # výška tabs baru
        self.header_gap = 16      # medzera pod tabs pred zoznamom
        self.list_top_gap = 50    # (rezervované – pre konzistentný layout)
        self.chip_radius = 14

        # Ovládanie
        self.controls = {
            1: {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT, 'select': pygame.K_RETURN},
            2: {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a,
                'right': pygame.K_d, 'select': pygame.K_LSHIFT},
        }

    # ----------------- Pomocné -----------------
    def _list_area(self, rect):
        x = rect.x + self.panel_pad
        y = rect.y + self.panel_pad + self.tab_height + self.header_gap
        w = rect.width - 2*self.panel_pad
        h = rect.height - (y - rect.y) - self.panel_pad - 30
        return pygame.Rect(x, y, w, max(60, h))

    def _visible_count(self, rect):
        area = self._list_area(rect)
        return max(1, area.height // self.row_spacing)

    def _clamp_scroll(self, player_id, tab, total, rect):
        vis = self._visible_count(rect)
        top = self.scroll_top[player_id][tab]
        sel = self.selected_index[player_id][tab]
        if sel < top:
            top = sel
        elif sel >= top + vis:
            top = sel - vis + 1
        top = max(0, min(max(0, total - vis), top))
        self.scroll_top[player_id][tab] = top

    # ----------------- Kreslenie UI -----------------
    def draw_panel(self, surface, rect):
        x, y, w, h = rect
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 20, 30, 200), (0, 0, w, h), border_radius=14)
        pygame.draw.rect(s, (255, 255, 255, 50), (0, 0, w, h), width=1, border_radius=14)
        surface.blit(s, (x, y))

    def blit_text_with_outline(self, surface, text, font, color, pos):
        x, y = pos
        outline = font.render(text, True, (0, 0, 0))
        for ox, oy in [(1,0),(-1,0),(0,1),(0,-1)]:
            surface.blit(outline, (x+ox, y+oy))
        surface.blit(font.render(text, True, color), (x, y))

    def draw_chip(self, surface, center, radius, color, disabled=False, selected=False, ring_color=None):
        r,g,b = color
        if disabled:
            r,g,b = int(r*0.4), int(g*0.4), int(b*0.4)
        pygame.draw.circle(surface, (r,g,b), center, radius)
        if selected:
            pygame.draw.circle(surface, ring_color or (255,255,255), center, radius + 6, 3)

    def draw_tab_bar(self, surface, rect, active_tab):
        tab_w = (rect.width - 2*self.panel_pad)
        x0 = rect.x + self.panel_pad
        y0 = rect.y + self.panel_pad
        half = tab_w // 2
        tabs = [
            pygame.Rect(x0, y0, half-4, self.tab_height),
            pygame.Rect(x0 + half + 4, y0, half-4, self.tab_height),
        ]
        for i, r in enumerate(tabs):
            bg = (40, 50, 70, 220) if i == active_tab else (25, 30, 45, 160)
            bar = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            pygame.draw.rect(bar, bg, bar.get_rect(), border_radius=10)
            pygame.draw.rect(bar, (255,255,255,70), bar.get_rect(), width=1, border_radius=10)
            surface.blit(bar, (r.x, r.y))
            label = config.TAB_NAMES[i]
            color = (255,255,255) if i == active_tab else (200,200,220)
            self.blit_text_with_outline(surface, label, self.small_font, color, (r.x+10, r.y+6))

    def tint_image(self, image, color):
        tinted = image.copy()
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))
        tinted.blit(tint, (0,0), special_flags=pygame.BLEND_MULT)
        return tinted

    def update_idle_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 2000/self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

    # ---- Zoznam Farieb (scroll) ----
    def draw_colors_list(self, screen, player_id, rect):
        area = self._list_area(rect)
        pygame.draw.rect(screen, (30, 38, 55), area, border_radius=10)

        # posun pre pravý panel (hráč 2)
        nudge = 0 if player_id == 1 else 12  # zmeň 12 -> koľko potrebuješ

        ring = config.COLOR_RED if player_id == 1 else config.COLOR_BLUE
        color_keys = list(AVAILABLE_COLORS.keys())
        total = len(color_keys)
        vis = self._visible_count(rect)
        top = self.scroll_top[player_id][config.TAB_COLORS]

        prev_clip = screen.get_clip()
        screen.set_clip(area)

        for i in range(vis):
            idx = top + i
            if idx >= total:
                break
            y = area.y + i*self.row_spacing + self.row_spacing//2

            if player_id == 1:
                cx = area.x + self.list_left_pad + nudge
                text_x = cx + 30
                align = "left"
            else:
                cx = area.right - self.list_left_pad - nudge
                text_x = cx - 30
                align = "right"

            chosen_by_other = (self.players[2]["color"] == color_keys[idx]) if player_id == 1 else (self.players[1]["color"] == color_keys[idx])
            selected = (self.selected_index[player_id][config.TAB_COLORS] == idx)
            self.draw_chip(screen, (cx, y), self.chip_radius, color_keys[idx], chosen_by_other, selected, ring)

            name = AVAILABLE_COLORS[color_keys[idx]]
            if align == "left":
                self.blit_text_with_outline(screen, name, self.info_font, (255,255,255), (text_x, y-12))
            else:
                w = self.info_font.size(name)[0]
                self.blit_text_with_outline(screen, name, self.info_font, (255,255,255), (text_x - w, y-12))

        screen.set_clip(prev_clip)
        self._draw_scrollbar(screen, area, top, vis, total)


    # ---- Zoznam Čiapok (scroll) ----
    def get_idle_frame_for_preview(self):
        """
        Vráti správny idle frame pre preview, prípadne posledný frame.
        """
        frames = self.images["idle"]
        # Použi frame_index cyklicky podľa času, aby animácia išla aj v preview
        now = pygame.time.get_ticks()
        frame_duration = 1000 // max(1, len(frames))  # dynamicky podľa počtu idle frames
        frame_index = (now // frame_duration) % len(frames)
        return frames[frame_index]

    


    def draw_hats_list(self, screen, player_id, rect):
        area = self._list_area(rect)

        # nepriehľadné prekrytie list oblasti
        pygame.draw.rect(screen, (30, 38, 55), area, border_radius=10)

        ring = config.COLOR_RED if player_id == 1 else config.COLOR_BLUE
        total = len(config.HATS)
        vis = self._visible_count(rect)
        top = self.scroll_top[player_id][config.TAB_HATS]

        prev_clip = screen.get_clip()
        screen.set_clip(area)

        for i in range(vis):
            idx = top + i
            if idx >= total:
                break
            hat = config.HATS[idx]
            y = area.y + i*self.row_spacing + self.row_spacing//2

            if player_id == 1:
                tx = area.x + self.list_left_pad - 10
                name_x = tx + 50
                thumb = self.hat_thumbs[hat["name"]]
                if thumb is not None:
                    screen.blit(thumb, (tx, y-18))
                self.blit_text_with_outline(screen, hat["name"], self.info_font, (230,230,240), (name_x, y-12))
            else:
                tx = area.right - self.list_left_pad - 8
                thumb = self.hat_thumbs[hat["name"]]
                if thumb is not None:
                    screen.blit(thumb, (tx - thumb.get_width(), y-18))
                    w = self.info_font.size(hat["name"])[0]
                    self.blit_text_with_outline(screen, hat["name"], self.info_font, (230,230,240),
                                                (tx - thumb.get_width() - 10 - w, y-12))
                else:
                    w = self.info_font.size(hat["name"])[0]
                    self.blit_text_with_outline(screen, hat["name"], self.info_font, (230,230,240),
                                                (tx - 10 - w, y-12))

            if self.selected_index[player_id][config.TAB_HATS] == idx:
                # border len vo vnútri list area
                inner = pygame.Rect(area.x+4, y - self.row_spacing//2 + 4, area.width-8, self.row_spacing-8)
                pygame.draw.rect(screen, ring, inner, width=2, border_radius=10)

        screen.set_clip(prev_clip)
        self._draw_scrollbar(screen, area, top, vis, total)

    def _draw_scrollbar(self, screen, area, top, vis, total):
        if total <= vis:
            return
        bar_w = 6
        x = area.right - bar_w - 4
        track = pygame.Rect(x, area.y+4, bar_w, area.height-8)
        pygame.draw.rect(screen, (80,90,110,160), track, border_radius=3)
        knob_h = max(20, int(track.height * (vis/total)))
        max_top = total - vis
        knob_y = track.y + int((top/max_top) * (track.height - knob_h))
        pygame.draw.rect(screen, (200,210,230,220), (x, knob_y, bar_w, knob_h), border_radius=3)

    # ---- Náhľad hráča (farba + čiapka) ----
    def draw_player_preview(self, screen, player_id, rect):
        color_keys = list(AVAILABLE_COLORS.keys())
        chosen_color = color_keys[self.selected_index[player_id][config.TAB_COLORS]]
        

        # --- Idle frame ---
        num_frames = len(self.idle_frames)
        frame_index = (pygame.time.get_ticks() // (1000 // self.idle_fps)) % num_frames
        
        frame = self.idle_frames[frame_index]
        img = self.tint_image(frame, chosen_color)
        if player_id == 2:
            img = pygame.transform.flip(img, True, False)

        px = rect.x + rect.width // 2 - img.get_width() // 2 + (45 if player_id == 1 else -45)
        py = rect.y + 72
        screen.blit(img, (px, py))
        # Čiapka presne podľa idle frame
        HAT_IDLE_OFFSETS = [0, -4, 0]  # normál → hore → stojí hore
        hat_offset = HAT_IDLE_OFFSETS[frame_index]
        # --- Hat ---
        hat_def = config.HATS[self.selected_index[player_id][config.TAB_HATS]]
        hat_name = hat_def["name"]
        if hat_name != "None":
            hat_img = self.hat_images.get(hat_name)
            if hat_img:
                ox, oy = hat_def["offset"]

                # --- Len pre čiapku "Devil" (rohy) ---
                if hat_name == "Devil":
                    if not hasattr(self, 'preview_corner_offset'):
                        self.preview_corner_offset = {1: 10, 2: -10}  # posuny pre ľavý/pravý preview
                    ox += self.preview_corner_offset.get(player_id, 0)

                hy = py + oy + hat_offset
                hx = px + ox

                if player_id == 2:
                    hat_img = pygame.transform.flip(hat_img, True, False)

                screen.blit(hat_img, (hx, hy))






    # ----------------- Draw -----------------
    def draw(self, screen):
        self.update_idle_animation()
        screen.fill((0, 0, 0))
        screen.blit(self.bg, (0, 0))

        # Panely
        self.draw_panel(screen, self.panel_rects[1])
        self.draw_panel(screen, self.panel_rects[2])

        # Nadpis
        title_img = pygame.transform.scale_by(self.title_img, 0.7)
        screen.blit(title_img, (40, -5))

        # Tabs
        self.draw_tab_bar(screen, self.panel_rects[1], self.active_tab[1])
        self.draw_tab_bar(screen, self.panel_rects[2], self.active_tab[2])

        # Zoznamy
        if self.active_tab[1] == config.TAB_COLORS:
            self.draw_colors_list(screen, 1, self.panel_rects[1])
        else:
            self.draw_hats_list(screen, 1, self.panel_rects[1])

        if self.active_tab[2] == config.TAB_COLORS:
            self.draw_colors_list(screen, 2, self.panel_rects[2])
        else:
            self.draw_hats_list(screen, 2, self.panel_rects[2])

        # Náhľady
        self.draw_player_preview(screen, 1, self.panel_rects[1])
        self.draw_player_preview(screen, 2, self.panel_rects[2])

        # Hinty
        p1_text = f"LEFT/RIGHT tab  •  UP/DOWN scroll  •  Enter"
        p2_text = f"A/D tab  •  W/S scroll  •  Shift"
        self.blit_text_with_outline(
            screen, p1_text, self.small_font, config.COLOR_RED,
            (self.panel_rects[1].x + self.panel_pad, self.panel_rects[1].bottom - 40)
        )
        self.blit_text_with_outline(
            screen, p2_text, self.small_font, config.COLOR_BLUE,
            (self.panel_rects[2].x + self.panel_pad, self.panel_rects[2].bottom - 40)
        )

        # Pokračovanie
        if self.players[1]["color"] and self.players[2]["color"]:
            cont = "Obaja vybrali – ENTER"
            cx = (config.SCREEN_WIDTH - self.font.size(cont)[0]) // 2
            self.blit_text_with_outline(screen, cont, self.font, (255,255,255), (cx, 24))


    # ----------------- Events -----------------
    def handle_events(self, event):
        color_keys = list(AVAILABLE_COLORS.keys())

        if event.type != pygame.KEYDOWN:
            return

        def total_count(tab):
            return len(color_keys) if tab == config.TAB_COLORS else len(config.HATS)

        # ================= PLAYER 1 =================
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
            # ✔ ENTER = vždy uloží FARBU AJ ČIAPKU
            color_idx = self.selected_index[1][config.TAB_COLORS]
            chosen_color = color_keys[color_idx]
            if chosen_color != self.players[2]["color"]:
                self.players[1]["color"] = chosen_color

            hat_idx = self.selected_index[1][config.TAB_HATS]
            self.players[1]["hat"] = config.HATS[hat_idx]["name"]

        # ================= PLAYER 2 =================
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

        # ================= POKRAČOVANIE =================
        if event.key == pygame.K_SPACE and self.players[1]["color"] and self.players[2]["color"]:
            payload = {
                1: (self.players[1]["color"], self.players[1]["hat"]),
                2: (self.players[2]["color"], self.players[2]["hat"]),
            }
            self.state_manager.change_state("MapSelector", payload)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))
        self.draw(screen)
