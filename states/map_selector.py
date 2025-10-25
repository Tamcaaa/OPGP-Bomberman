import pygame
import random
import config
import os
from states.state import State
from maps.test_field_map import all_maps
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
        self.bg = pygame.image.load(os.path.join(game.photos_dir, "battlefield-bg.png"))
        self.text = pygame.image.load(os.path.join(game.photos_dir, "battlefield.png"))

        self.selected_maps = []
        self.final_map = None
        self.music_manager = MusicManager()
        self.state_manager = StateManager(self.game)

        self.players = {
            1: PlayerSelection(),
            2: PlayerSelection()
        }

        self.all_maps = all_maps

        # Fonts
        self.title_font = pygame.font.Font("CaveatBrush-Regular.ttf", 46)
        self.map_font = pygame.font.SysFont('Arial', 26)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 25)

        # UI parameters
        self.card_width = 250
        self.card_height = 160
        self.card_spacing = 30
        self.card_radius = 15

        self.select_random_maps()

    def select_random_maps(self):
        available_maps = list(self.all_maps.items())
        self.selected_maps = random.sample(available_maps, min(3, len(available_maps)))

    def move_selection(self, player_id, direction):
        player = self.players[player_id]
        player.selection_index = (player.selection_index + direction) % len(self.selected_maps)

    def confirm_vote(self, player_id):
        player = self.players[player_id]
        player.vote_index = player.selection_index

        if all(p.vote_index is not None for p in self.players.values()):
            self.determine_final_map()

    def determine_final_map(self):
        votes = [p.vote_index for p in self.players.values() if p.vote_index is not None]
        vote_counts = {idx: votes.count(idx) for idx in set(votes)}
        winning_index = max(vote_counts, key=vote_counts.get)
        self.final_map = self.selected_maps[winning_index]

    def draw_card(self, screen, i, map_name):
        map_count = len(self.selected_maps)
        total_width = map_count * self.card_width + (map_count - 1) * self.card_spacing
        start_x = (config.SCREEN_WIDTH - total_width) // 2
        x = start_x + i * (self.card_width + self.card_spacing)
        y = config.SCREEN_HEIGHT // 2 - self.card_height // 2

        # Card background
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(screen, config.COLOR_BEIGE, rect, border_radius=self.card_radius)

        # Selected border
        for pid, color in [(1, (200, 50, 50)), (2, (50, 150, 250))]:
            player = self.players[pid]
            if player.selection_index == i:
                pygame.draw.rect(screen, color, rect, 4, border_radius=self.card_radius)

        # Map name text
        text_surf = self.map_font.render(map_name, True, config.TEXT_COLOR)
        screen.blit(text_surf, (x + self.card_width // 2 - text_surf.get_width() // 2, y + 10))

        # Map preview if available
        try:
            preview_img = pygame.image.load(os.path.join("assets", "map_previews",
                                                         f"{map_name.lower().replace(' ', '_')}_preview.png"))
            preview_img = pygame.transform.scale(preview_img, (self.card_width - 20, self.card_height - 50))
            screen.blit(preview_img, (x + 10, y + 40))
        except:
            pass

    def render(self, screen):
        screen.blit(self.bg, (0, 0))

        battlefield_img = pygame.image.load(os.path.join("assets", "battlefield.png"))

        screen.blit(battlefield_img, (config.SCREEN_WIDTH // 2 - battlefield_img.get_width() // 2, 40))

        # Draw map cards
        for i, (name, _) in enumerate(self.selected_maps):
            self.draw_card(screen, i, name)

        # Instructions
        p1_instr = "Player 1: <- -> to move, ENTER to vote" if self.players[1].vote_index is None else "Vote confirmed!"
        p2_instr = "Player 2: A D to move, RIGHT SHIFT to vote" if self.players[
                                                                       2].vote_index is None else "Vote confirmed!"

        screen.blit(self.info_font.render(p1_instr, True, (200, 50, 50)), (50, config.SCREEN_HEIGHT - 80))
        screen.blit(self.info_font.render(p2_instr, True, (50, 150, 250)),
                    (config.SCREEN_WIDTH - 50 - self.info_font.size(p2_instr)[0], config.SCREEN_HEIGHT - 80))

        # Final map overlay
        if self.final_map:
            map_name = self.final_map[0]
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))

            # Centered text
            text_surf = self.title_font.render(f"{map_name} Selected!", True, (0, 255, 255))
            screen.blit(text_surf,
                        (config.SCREEN_WIDTH // 2 - text_surf.get_width() // 2, config.SCREEN_HEIGHT // 2 - 50))

            start_text = self.info_font.render("Press SPACE to start", True, (255, 255, 0))
            screen.blit(start_text,
                        (config.SCREEN_WIDTH // 2 - start_text.get_width() // 2, config.SCREEN_HEIGHT // 2 + 20))

    def update(self):
        pass  # Minimal/no animations

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
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
                map_name = self.final_map[0]
                selected_map = self.final_map[1]
                self.state_manager.change_state("TestField", selected_map, map_name, selected_skins=self.selected_skins)