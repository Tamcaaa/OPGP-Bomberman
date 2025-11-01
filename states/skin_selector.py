import pygame, os
from states.state import State
import config
from managers.state_manager import StateManager

# Dostupné farby
AVAILABLE_COLORS = {
    config.WHITE_PLAYER: "White",
    config.BLACK_PLAYER: "Black",
    config.RED_PLAYER: "Red",
    config.BLUE_PLAYER: "Blue",
    config.GREEN_PLAYER: "Green",
    config.YELLOW_PLAYER: "Yellow",
}

class SkinSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Skin Selection")
        self.state_manager = StateManager(self.game)

        self.bg = pygame.image.load(os.path.join(game.photos_dir, "skinselector_bg.png")).convert()

        # Sprites hráča
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

        self.players = {1: None, 2: None}
        self.selected_index = {1: 0, 2: 0}

        self.font = pygame.font.Font("CaveatBrush-Regular.ttf", 28)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 22)

        self.panel_rects = {
            1: pygame.Rect(40, 70, 320, 380),
            2: pygame.Rect(config.SCREEN_WIDTH - 360, 70, 320, 380),
        }
        self.panel_pad = 20
        self.row_spacing = 54
        self.chip_radius = 16

        self.controls = {
            1: {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'select': pygame.K_RETURN},
            2: {'up': pygame.K_w, 'down': pygame.K_s, 'select': pygame.K_LSHIFT},
        }

    # PANEL
    def draw_panel(self, surface, rect):
        x, y, w, h = rect
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 20, 30, 200), (0, 0, w, h), border_radius=14)
        pygame.draw.rect(s, (255, 255, 255, 50), (0, 0, w, h), width=1, border_radius=14)
        surface.blit(s, (x, y))

    # TEXT OUTLINE
    def blit_text_with_outline(self, surface, text, font, color, pos):
        x, y = pos
        outline = font.render(text, True, (0, 0, 0))
        for ox, oy in [(1,0),(-1,0),(0,1),(0,-1)]:
            surface.blit(outline, (x+ox, y+oy))
        surface.blit(font.render(text, True, color), (x, y))

    # CHIPS
    def draw_chip(self, surface, center, radius, color, disabled=False, selected=False, player_id=None):
        r,g,b = color
        if disabled:
            r,g,b = int(r*0.4), int(g*0.4), int(b*0.4)
        pygame.draw.circle(surface, (r,g,b), center, radius)
        if selected:
            if player_id == 1:
                pygame.draw.circle(surface, config.COLOR_RED, center, radius + 6, 3)
            elif player_id == 2:
                pygame.draw.circle(surface, config.COLOR_BLUE, center, radius + 6, 3)
            

    # SPRITE COLORING
    def tint_image(self, image, color):
        tinted = image.copy()
        tinted.fill(color, special_flags=pygame.BLEND_MULT)
        return tinted

    def update_idle_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 1000/self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

    # DRAW UI
    def draw(self, screen):
        self.update_idle_animation()
        screen.blit(self.bg, (0, 0))

        color_keys = list(AVAILABLE_COLORS.keys())
        y_start = self.panel_rects[1].y + 80

        # Panely
        self.draw_panel(screen, self.panel_rects[1])
        self.draw_panel(screen, self.panel_rects[2])

        # Titulky
        self.blit_text_with_outline(screen, "Skin Selection", self.font, (255,255,255), (40, 20))
        self.blit_text_with_outline(screen, "Player 1", self.font, config.COLOR_RED,
                                    (self.panel_rects[1].x+self.panel_pad, self.panel_rects[1].y+16))
        self.blit_text_with_outline(screen, "Player 2", self.font, config.COLOR_BLUE,
                                    (self.panel_rects[2].x+self.panel_pad, self.panel_rects[2].y+16))

        # Chips
        for idx, color in enumerate(color_keys):
            cy = y_start + idx*self.row_spacing
            name = AVAILABLE_COLORS[color]

            # P1 chips vľavo
            cx1 = self.panel_rects[1].x + self.panel_pad + 24
            disabled_p1 = (self.players[2] == color)
            sel_p1 = (self.selected_index[1] == idx)
            self.draw_chip(screen, (cx1,cy), self.chip_radius, color, disabled_p1, sel_p1, player_id=1)
            self.blit_text_with_outline(screen, name, self.info_font, (255,255,255),
                                        (cx1+30, cy-12))

            # P2 chips vpravo (zrkadlovo)
            cx2 = self.panel_rects[2].right - self.panel_pad - 24
            disabled_p2 = (self.players[1] == color)
            sel_p2 = (self.selected_index[2] == idx)
            self.draw_chip(screen, (cx2,cy), self.chip_radius, color, disabled_p2, sel_p2, player_id=2)
            w = self.info_font.size(name)[0]
            self.blit_text_with_outline(screen, name, self.info_font, (255,255,255),
                                        (cx2 - 30 - w, cy - 12))

        # Sprite preview
        frame = self.idle_frames[self.idle_index]
        p1_img = self.tint_image(frame, color_keys[self.selected_index[1]])
        p2_img = self.tint_image(frame, color_keys[self.selected_index[2]])
        p2_img = pygame.transform.flip(p2_img, True, False)

        preview_y = self.panel_rects[1].y + 80
        screen.blit(p1_img, (self.panel_rects[1].x + self.panel_pad + 50, preview_y))
        screen.blit(p2_img, (self.panel_rects[2].x + self.panel_pad - 25, preview_y))

        # Hinty ovládania
        p1_text = "ENTER potvrď" if self.players[1] else "Šípky  • Enter"
        p2_text = "SHIFT potvrď" if self.players[2] else "W/S • Shift"

        self.blit_text_with_outline(screen, p1_text, self.info_font, config.COLOR_RED,
                                    (self.panel_rects[1].x + self.panel_pad,
                                     self.panel_rects[1].y + self.panel_rects[1].height - 0))
        self.blit_text_with_outline(screen, p2_text, self.info_font, config.COLOR_BLUE,
                                    (self.panel_rects[2].x + self.panel_pad,
                                     self.panel_rects[2].y + self.panel_rects[2].height - 0))

        # Pokračovanie
        if all(self.players.values()):
            cont = "Obaja vybrali – ENTER"
            cx = (config.SCREEN_WIDTH - self.font.size(cont)[0]) // 2
            self.blit_text_with_outline(screen, cont, self.font, (255,255,255), (cx, 24))

        pygame.display.flip()

    def handle_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        color_keys = list(AVAILABLE_COLORS.keys())

        if event.key == self.controls[1]['up']:
            self.selected_index[1] = (self.selected_index[1]-1) % len(color_keys)
        elif event.key == self.controls[1]['down']:
            self.selected_index[1] = (self.selected_index[1]+1) % len(color_keys)
        elif event.key == self.controls[1]['select']:
            chosen = color_keys[self.selected_index[1]]
            if chosen != self.players[2]:
                self.players[1] = chosen

        if event.key == self.controls[2]['up']:
            self.selected_index[2] = (self.selected_index[2]-1) % len(color_keys)
        elif event.key == self.controls[2]['down']:
            self.selected_index[2] = (self.selected_index[2]+1) % len(color_keys)
        elif event.key == self.controls[2]['select']:
            chosen = color_keys[self.selected_index[2]]
            if chosen != self.players[1]:
                self.players[2] = chosen

        # Enter až po vybraní farieb
        if event.key == pygame.K_RETURN and all(self.players.values()):
            self.state_manager.change_state("MapSelector", self.players)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))
        self.draw(screen)
