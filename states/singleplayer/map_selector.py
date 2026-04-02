import pygame
import random
import config
import os
from states.general.state import State
from maps.test_field_map import MAP_NAMES, get_map
from dataclasses import dataclass
from managers.music_manager import MusicManager
from managers.state_manager import StateManager

@dataclass
class PlayerSelection:
    selection_index: int = 0
    vote_index: int | None = None


class MapSelector(State):
    def __init__(self, game, selected_skins=None):
        super().__init__(game)
        self.selected_skins = selected_skins or {}
        pygame.display.set_caption("BomberMan: Map Selection")

        # Pozadie – rovnaký prístup ako SkinSelector
        try:
            self.bg = pygame.image.load(
                os.path.join(game.photos_dir, "battlefield-bg.png")
            ).convert()
        except Exception:
            self.bg = None

        self.selected_maps = []
        self.final_map = None
        self.music_manager = MusicManager()
        self.state_manager = StateManager(self.game)

        self.players = {
            1: PlayerSelection(),
            2: PlayerSelection()
        }

        # Fonty – rovnaký CaveatBrush ako SkinSelector
        self.font_lg = pygame.font.Font("CaveatBrush-Regular.ttf", 30)
        self.font_md = pygame.font.Font("CaveatBrush-Regular.ttf", 22)
        self.font_sm = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
        self.font_xs = pygame.font.Font("CaveatBrush-Regular.ttf", 15)

        # Karta
        self.card_w      = config.CARD_W
        self.card_h      = config.CARD_H
        self.card_gap    = config.CARD_GAP
        self.card_radius = config.CARD_RADIUS
        self.card_y      = config.SCREEN_HEIGHT // 2 - 80

        self.select_random_maps()

        # Animácia final overlay (fade in)
        self.overlay_alpha = config.OVERLAY_ALPHA

    # ------------------------------------------------------------------ helpers
    def _player_color(self, player_id: int) -> tuple:
        """Živá farba hráča z selected_skins."""
        if player_id in self.selected_skins:
            return self.selected_skins[player_id][0]
        return (232, 230, 240)

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
        """Vrchný glow – rovnaký efekt ako na paneloch v SkinSelector."""
        glow = pygame.Surface((rect.width, 6), pygame.SRCALPHA)
        for gx in range(rect.width):
            a = int(alpha * (1 - abs(gx - rect.width / 2) / (rect.width / 2)))
            pygame.draw.line(glow, (*color, a), (gx, 0), (gx, 5))
        screen.blit(glow, (rect.x, rect.y))

    # ------------------------------------------------------------------ logic
    def select_random_maps(self):
        self.selected_maps = random.sample(MAP_NAMES, min(3, len(MAP_NAMES)))

    def move_selection(self, player_id, direction):
        p = self.players[player_id]
        p.selection_index = (p.selection_index + direction) % len(self.selected_maps)

    def confirm_vote(self, player_id):
        self.players[player_id].vote_index = self.players[player_id].selection_index
        if all(p.vote_index is not None for p in self.players.values()):
            self.determine_final_map()

    def determine_final_map(self):
        votes = [p.vote_index for p in self.players.values() if p.vote_index is not None]
        vote_counts = {idx: votes.count(idx) for idx in set(votes)}
        winning_index = max(vote_counts, key=vote_counts.get)
        self.final_map = self.selected_maps[winning_index]  # string

    # ------------------------------------------------------------------ card
    def _card_x(self, i):
        total_w = len(self.selected_maps) * self.card_w + (len(self.selected_maps) - 1) * self.card_gap
        start_x = (config.SCREEN_WIDTH - total_w) // 2
        return start_x + i * (self.card_w + self.card_gap)

    def draw_card(self, screen, i, map_name):
        x = self._card_x(i)
        y = self.card_y
        rect = pygame.Rect(x, y, self.card_w, self.card_h)

        # Zisti či niekto hráč ukazuje na túto kartu
        p1_here = self.players[1].selection_index == i
        p2_here = self.players[2].selection_index == i
        p1_voted = self.players[1].vote_index == i
        p2_voted = self.players[2].vote_index == i

        # Pozadie karty
        self._draw_rrect(screen, config.BG_PANEL, rect, radius=self.card_radius, alpha=220)

        # Map preview obrázok
        try:
            preview = pygame.image.load(
                os.path.join("assets", "map_previews",
                             f"{map_name.lower().replace(' ', '_')}_preview.png")
            ).convert()
            preview = pygame.transform.smoothscale(preview, (self.card_w - 20, self.card_h - 50))
            preview_rect = pygame.Rect(x + 10, y + 36, self.card_w - 20, self.card_h - 50)
            screen.blit(preview, preview_rect.topleft)
            # Jemný overlay na preview aby text bol čitateľný
            ov = pygame.Surface((self.card_w - 20, self.card_h - 50), pygame.SRCALPHA)
            ov.fill((10, 12, 18, 60))
            screen.blit(ov, preview_rect.topleft)
        except Exception:
            # Placeholder ak nie je preview
            ph = pygame.Rect(x + 10, y + 36, self.card_w - 20, self.card_h - 50)
            self._draw_rrect(screen, config.BG_LIST, ph, radius=8, alpha=180)
            self._text(screen, "no preview", self.font_xs, config.TEXT_HINT,
                       (ph.centerx, ph.centery - 8), align="center")

        # Meno mapy
        self._text(screen, map_name, self.font_sm, config.TEXT_PRIMARY,
                   (x + self.card_w // 2, y + 10), align="center")

        # Orámovanie podľa hráčov – P1 a P2 môžu byť na tej istej karte
        borders = []
        if p1_here or p1_voted:
            borders.append((self._player_color(1), 3 if p1_voted else 2))
        if p2_here or p2_voted:
            borders.append((self._player_color(2), 3 if p2_voted else 2))

        if len(borders) == 2:
            # Obaja na tej istej karte – rozdelíme okraj na dve polovice
            c1, w1 = borders[0]
            c2, w2 = borders[1]
            # Ľavá polovica = P1, pravá = P2
            pygame.draw.rect(screen, c1, pygame.Rect(x, y, self.card_w // 2, self.card_h),
                             width=w1, border_top_left_radius=self.card_radius,
                             border_bottom_left_radius=self.card_radius)
            pygame.draw.rect(screen, c2, pygame.Rect(x + self.card_w // 2, y, self.card_w // 2, self.card_h),
                             width=w2, border_top_right_radius=self.card_radius,
                             border_bottom_right_radius=self.card_radius)
        elif len(borders) == 1:
            c, w = borders[0]
            pygame.draw.rect(screen, c, rect, width=w, border_radius=self.card_radius)
            # Glow nad kartou v farbe hráča
            self._glow_line(screen, rect, c, alpha=80)

        # Vote badge – malý krúžok s farbou hráča ak voted
        badge_x = x + self.card_w - 14
        badge_y = y + 14
        if p1_voted:
            pygame.draw.circle(screen, self._player_color(1), (badge_x - 14, badge_y), 7)
        if p2_voted:
            pygame.draw.circle(screen, self._player_color(2), (badge_x, badge_y), 7)

    # ------------------------------------------------------------------ render
    def render(self, screen):
        # Pozadie
        screen.fill(config.BG_BASE)
        if self.bg:
            bg_s = pygame.transform.scale(self.bg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            dark = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            dark.fill((10, 12, 18, 180))
            screen.blit(bg_s, (0, 0))
            screen.blit(dark, (0, 0))

        # Nadpis
        self._text(screen, "BOMBERMAN", self.font_lg, config.TEXT_PRIMARY,
                   (config.SCREEN_WIDTH // 2, 10), align="center")
        self._text(screen, "CHOOSE YOUR BATTLEFIELD", self.font_xs, config.TEXT_MUTED,
                   (config.SCREEN_WIDTH // 2, 38), align="center")

        # Karty
        for i, name in enumerate(self.selected_maps):
            self.draw_card(screen, i, name)

        # Player hint bary – rovnaký štýl ako SkinSelector hint bar
        self._draw_player_hint(screen, 1)
        self._draw_player_hint(screen, 2)

        # Final map overlay
        if self.final_map:
            self._draw_final_overlay(screen)

    def _draw_player_hint(self, screen, player_id):
        c = self._player_color(player_id)
        voted = self.players[player_id].vote_index is not None

        if player_id == 1:
            nav    = "LEFT/RIGHT  move"
            action = "Enter  =  vote" if not voted else "\u2022  voted"
            cx = 80
        else:
            nav    = "A D  move"
            action = "Shift  =  vote" if not voted else "\u2022  voted"
            cx = config.SCREEN_WIDTH - 80

        hy = config.SCREEN_HEIGHT - 52
        self._text(screen, nav,    self.font_xs, config.TEXT_HINT, (cx, hy),      align="center")
        self._text(screen, action, self.font_xs, c,         (cx, hy + 18), align="center")

    def _draw_final_overlay(self, screen):
        # Fade-in alpha
        self.overlay_alpha = min(self.overlay_alpha + 6, 210)

        ov = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 12, 18, self.overlay_alpha))
        screen.blit(ov, (0, 0))

        if self.overlay_alpha < 100:
            return

        map_name = self.final_map

        # Centrálny panel
        pw, ph = 420, 120
        px = config.SCREEN_WIDTH // 2 - pw // 2
        py = config.SCREEN_HEIGHT // 2 - ph // 2
        panel = pygame.Rect(px, py, pw, ph)

        self._draw_rrect(screen, config.BG_PANEL, panel, radius=18, alpha=230,
                         border=1, border_color=config.BTN_BEIGE)
        self._glow_line(screen, panel, config.BTN_BEIGE, alpha=100)

        self._text(screen, map_name.upper(), self.font_lg, config.BTN_BEIGE,
                   (config.SCREEN_WIDTH // 2, py + 18), align="center")
        self._text(screen, "SELECTED", self.font_xs, config.TEXT_MUTED,
                   (config.SCREEN_WIDTH // 2, py + 52), align="center")

        # SPACE button
        bw = self.font_md.size("SPACE  –  LET'S PLAY")[0] + 40
        bh = 36
        bx = config.SCREEN_WIDTH // 2 - bw // 2
        by = py + ph + 16
        self._draw_rrect(screen, config.BTN_BEIGE, pygame.Rect(bx, by, bw, bh), radius=12)
        self._text(screen, "SPACE  –  LET'S PLAY", self.font_md, config.BG_BASE,
                   (config.SCREEN_WIDTH // 2, by + 7), align="center")

    # ------------------------------------------------------------------ update / events
    def update(self):
        pass

    def handle_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_LEFT:
            self.move_selection(1, -1)
        elif event.key == pygame.K_RIGHT:
            self.move_selection(1, 1)
        elif event.key == pygame.K_RETURN:
            if self.players[1].vote_index is None:
                self.confirm_vote(1)

        if event.key == pygame.K_a:
            self.move_selection(2, -1)
        elif event.key == pygame.K_d:
            self.move_selection(2, 1)
        elif event.key == pygame.K_RSHIFT:
            if self.players[2].vote_index is None:
                self.confirm_vote(2)

        if event.key == pygame.K_SPACE and self.final_map:
            map_name = self.final_map
            selected_map = get_map(map_name)  
            self.state_manager.change_state(
                "TestField", selected_map, map_name, selected_skins=self.selected_skins
            )