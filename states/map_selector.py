from typing import Dict

import pygame
import random
import config
import os
from managers.music_manager import MusicManager
from states.state import State
from maps.test_field_map import all_maps
from collections import Counter


class MapSelector(State):

    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: MapSelection")
        self.selected_maps = []
        self.player_votes = {1: None, 2: None}
        self.player_selection = {1: 0, 2: 0}  # Current index selection
        self.final_map = None
        self.music_manager = MusicManager()

        self.all_maps = all_maps

        # Enhanced fonts
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.map_font = pygame.font.SysFont('Arial', 28)
        self.info_font = pygame.font.SysFont('Arial', 22)
        self.instruction_font = pygame.font.SysFont('Arial', 20)
        self.bg_image = pygame.image.load(os.path.join("assets", "bg.png"))

        # Animation variables
        self.animation_timer = 30
        self.transition_effect = 1.0
        self.vote_flash_timer = {1: 0, 2: 0}

        # Select initial maps
        self.select_random_maps()

    def select_random_maps(self):
        available_maps = list(self.all_maps.items())
        count = min(3, len(available_maps))
        self.selected_maps = random.sample(available_maps, count)

    def move_selection(self, player_id, direction):
        if player_id in self.player_selection:
            current = self.player_selection[player_id]
            self.player_selection[player_id] = (current + direction) % len(self.selected_maps)
            # self.music_manager.play_sound("move_map_selector")

    def confirm_vote(self, player_id):
        self.player_votes[player_id] = self.player_selection.get(player_id)
        self.vote_flash_timer[player_id] = 30  # Start vote flash animation
        # self.music_manager.play_music("select_map_selector")
        if all(vote is not None for vote in self.player_votes.values()):
            self.determine_final_map()

    def determine_final_map(self):
        votes = [vote for vote in self.player_votes.values() if vote is not None]
        vote_counter = Counter(votes)
        max_votes = max(vote_counter.values())
        top_maps = [index for index, count in vote_counter.items() if count == max_votes]
        winning_index = random.choice(top_maps) if len(top_maps) > 1 else top_maps[0]
        self.final_map = self.selected_maps[winning_index]
        self.animation_timer = 60  # Animation frames for final selection
        # self.music_manager.play_music("final_map_selector")

    def get_final_map(self):
        return self.final_map

    def update_animations(self):
        # Update animation timers
        if self.animation_timer > 0:
            self.animation_timer -= 1

        if self.transition_effect > 0:
            self.transition_effect = max(0, self.transition_effect - 0.02)

        for player in self.vote_flash_timer:
            if self.vote_flash_timer[player] > 0:
                self.vote_flash_timer[player] -= 1

    def draw_player_indicators(self, screen):
        # Draw player selection indicators
        for player_id in [1, 2]:
            if self.player_selection[player_id] >= len(self.selected_maps):
                continue

            selection_idx = self.player_selection[player_id]
            map_count = len(self.selected_maps)

            # Calculate x position based on the card position
            card_width = 240
            card_spacing = 60  # Space between cards
            total_width = (card_width * map_count) + (card_spacing * (map_count - 1))
            start_x = (config.SCREEN_WIDTH - total_width) // 2
            x = start_x + (card_width + card_spacing) * selection_idx + card_width // 2

            y = config.SCREEN_HEIGHT // 2 - 120

            color = config.SELECTOR_COLORS['p1'] if player_id == 1 else config.SELECTOR_COLORS['p2']

            # Draw a small colored square instead of the triangle
            indicator_size = 10
            square_rect = pygame.Rect(
                x - indicator_size // 2,
                y - 30,  # Positioned above the cards
                indicator_size,
                indicator_size
            )
            pygame.draw.rect(screen, color, square_rect)

            # Removed the player label (P1/P2 text) as requested

    @staticmethod
    def draw_rounded_rect(surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle"""
        rect = pygame.Rect(rect)

        # Draw the main rectangle body
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

        # If it's not a border (filled rect), return early
        if border_width == 0:
            return

        # For border, we need to draw it again with proper border radius
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

    def draw_map_cards(self, screen):
        map_count = len(self.selected_maps)
        card_width = 240
        card_height = 180
        card_spacing = 60  # Space between cards

        # Calculate total width of all cards + spacing
        total_width = (card_width * map_count) + (card_spacing * (map_count - 1))
        start_x = (config.SCREEN_WIDTH - total_width) // 2

        for i, (name, map_data) in enumerate(self.selected_maps):
            # Calculate position with spacing
            x = start_x + (card_width + card_spacing) * i
            y = config.SCREEN_HEIGHT // 2 - card_height // 2

            # Apply entrance animation
            if self.animation_timer > 0:
                offset = (30 - min(30, self.animation_timer)) / 30
                y = y + (1 - offset) * 300

            # Create card rect
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Determine if this card is selected by either player
            p1_selected = self.player_selection[1] == i
            p2_selected = self.player_selection[2] == i
            p1_voted = self.player_votes[1] == i
            p2_voted = self.player_votes[2] == i

            # Draw card background with rounded corners (radius of 15)
            self.draw_rounded_rect(screen, config.SELECTOR_COLORS['map_bg'], card_rect, 15)

            # Draw selection border with rounded corners
            border_width = 3
            if p1_selected and p2_selected:
                # Purple border for both players
                self.draw_rounded_rect(screen, (170, 50, 170), card_rect, 15, border_width)
            elif p1_selected:
                # Red border for player 1
                self.draw_rounded_rect(screen, config.SELECTOR_COLORS['p1'], card_rect, 15, border_width)
            elif p2_selected:
                # Blue border for player 2
                self.draw_rounded_rect(screen, config.SELECTOR_COLORS['p2'], card_rect, 15, border_width)
            else:
                # Default border
                self.draw_rounded_rect(screen, config.SELECTOR_COLORS['map_border'], card_rect, 15, border_width)

            # Draw map name
            name_text = self.map_font.render(name, True, config.SELECTOR_COLORS['text'])
            screen.blit(name_text, (x + card_width // 2 - name_text.get_width() // 2, y + 20))

            # Draw vote indicators
            vote_y = y + card_height - 40

            if p1_voted:
                flash_effect = self.vote_flash_timer[1] > 0 and self.vote_flash_timer[1] % 10 < 5
                vote_color = (255, 255, 255) if flash_effect else config.SELECTOR_COLORS['p1']
                vote_text = self.info_font.render("P1 Vote", True, vote_color)
                screen.blit(vote_text, (x + 20, vote_y))

            if p2_voted:
                flash_effect = self.vote_flash_timer[2] > 0 and self.vote_flash_timer[2] % 10 < 5
                vote_color = (255, 255, 255) if flash_effect else config.SELECTOR_COLORS['p2']
                vote_text = self.info_font.render("P2 Vote", True, vote_color)
                screen.blit(vote_text, (x + card_width - 20 - vote_text.get_width(), vote_y))

            # Highlight the winning map with rounded corners
            if self.final_map and self.final_map[0] == name:
                highlight_size = min(20, self.animation_timer) / 2
                highlight_rect = card_rect.inflate(highlight_size, highlight_size)
                self.draw_rounded_rect(screen, config.SELECTOR_COLORS['highlight'], highlight_rect, 18, 4)

    def draw_instructions(self, screen):
        # Player 1 instructions
        if self.player_votes[1] is None:
            p1_text = "Player 1: ← → to move, ENTER to vote"
        else:
            p1_text = "Player 1: Vote confirmed!"

        p1_instr = self.instruction_font.render(p1_text, True, config.SELECTOR_COLORS['p1'])
        screen.blit(p1_instr, (50, config.SCREEN_HEIGHT - 80))

        # Player 2 instructions
        if self.player_votes[2] is None:
            p2_text = "Player 2: A D to move, RIGHT SHIFT to vote"
        else:
            p2_text = "Player 2: Vote confirmed!"

        p2_instr = self.instruction_font.render(p2_text, True, config.SELECTOR_COLORS['p2'])
        screen.blit(p2_instr, (config.SCREEN_WIDTH - 50 - p2_instr.get_width(), config.SCREEN_HEIGHT - 80))

    def render(self, screen):
        if self.final_map:
            # Draw semi-transparent overlay with darker background
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            # Increased alpha value for a darker overlay (from 150 to 200)
            overlay.fill((0, 0, 0, min(255, self.animation_timer * 6)))
            screen.blit(overlay, (0, 0))

            # Draw final selection announcement with rounded background
            map_name_text = self.title_font.render(f"{self.final_map[0]}", True, (0, 255, 255))
            text_x = config.SCREEN_WIDTH // 2 - map_name_text.get_width() // 2
            text_y = config.SCREEN_HEIGHT // 2 - 50

            # Add glow effect with rounded corners and darker background
            # Make a larger background for the announcement
            announcement_bg = pygame.Surface((map_name_text.get_width() + 80, map_name_text.get_height() + 100), pygame.SRCALPHA)
            bg_rect = announcement_bg.get_rect()
            # Darker, more opaque background (50, 50, 60, 230)
            pygame.draw.rect(announcement_bg, (20, 20, 30, 230), bg_rect, border_radius=20)
            screen.blit(announcement_bg, (text_x - 40, text_y - 30))

            # Add glow effect with rounded corners
            glow_surf = pygame.Surface((map_name_text.get_width() + 20, map_name_text.get_height() + 20), pygame.SRCALPHA)
            glow_rect = glow_surf.get_rect()
            pygame.draw.rect(glow_surf, (0, 200, 255, 120), glow_rect, border_radius=15)
            screen.blit(glow_surf, (text_x - 10, text_y - 10))

            # Draw the map name first
            screen.blit(map_name_text, (text_x, text_y))

            # Draw "Selected Map" text underneath
            selected_label = self.info_font.render("Selected Map", True, (200, 200, 200))
            screen.blit(selected_label,
                        (config.SCREEN_WIDTH // 2 - selected_label.get_width() // 2, text_y + map_name_text.get_height() + 10))

            # Draw start instruction
            start_text = self.info_font.render("Press SPACE to start the game", True, (255, 255, 0))
            screen.blit(start_text, (config.SCREEN_WIDTH // 2 - start_text.get_width() // 2, text_y + map_name_text.get_height() + 50))
        else:
            screen.blit(self.bg_image, (0, 0))

            # Draw title with slight bounce effect
            title = self.title_font.render("SELECT YOUR BATTLEFIELD", True, config.SELECTOR_COLORS['title'])
            screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

            # Draw map cards
            self.draw_map_cards(screen)

            # Draw player selection indicators
            self.draw_player_indicators(screen)

            # Draw instructions
            self.draw_instructions(screen)

        # Apply transition effect
        if self.transition_effect > 0:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int(255 * self.transition_effect))
            screen.blit(overlay, (0, 0))

    def update(self):
        self.update_animations()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            # Player 1: LEFT / RIGHT to move, RETURN to confirm
            if event.key == pygame.K_LEFT:
                self.move_selection(1, -1)
            elif event.key == pygame.K_RIGHT:
                self.move_selection(1, 1)
            elif event.key == pygame.K_RETURN:
                if self.player_votes[1] is None:
                    self.confirm_vote(1)

            # Player 2: A / D to move, RSHIFT to confirm
            elif event.key == pygame.K_a:
                self.move_selection(2, -1)
            elif event.key == pygame.K_d:
                self.move_selection(2, 1)
            elif event.key == pygame.K_RSHIFT:
                if self.player_votes[2] is None:
                    self.confirm_vote(2)

            # If space is pressed and the final map is selected, exit the loop
            if event.key == pygame.K_SPACE and self.final_map:
                self.exit_state()
                from states.test_field import TestField
                map_name = self.final_map[0]
                selected_map = self.final_map[1]
                new_state = TestField(self.game, selected_map, map_name)
                new_state.enter_state()
