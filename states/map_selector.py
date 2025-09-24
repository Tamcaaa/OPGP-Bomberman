import pygame
import random
import config
import os
from states.state import State
from maps.test_field_map import all_maps
from collections import Counter
from dataclasses import dataclass
from managers.music_manager import MusicManager
from managers.state_manager import StateManager


@dataclass
class PlayerSelection:
    selection_index: int = 0
    vote_index: int | None = None
    vote_flash_timer: int = 0


class MapSelector(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: MapSelection")
        self.selected_maps = []
        self.final_map = None
        self.music_manager = MusicManager()
        self.state_manager = StateManager(self.game)

        self.players = {
            1: PlayerSelection(),
            2: PlayerSelection()
        }
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

        # Select initial maps
        self.select_random_maps()

    def select_random_maps(self):
        available_maps = list(self.all_maps.items())
        count = min(3, len(available_maps))
        self.selected_maps = random.sample(available_maps, count)

    def move_selection(self, player_id, direction):
        if player_id in self.players:
            current = self.players[player_id].selection_index
            self.players[player_id].selection_index = (current + direction) % len(self.selected_maps)
            # self.music_manager.play_sound("move_map_selector")

    def confirm_vote(self, player_id):
        player = self.players[player_id]
        player.vote_index = player.selection_index
        player.vote_flash_timer = 30
        if all(p.vote_index is not None for p in self.players.values()):
            self.determine_final_map()

    def determine_final_map(self):
        votes = [p.vote_index for p in self.players.values() if p.vote_index is not None]
        vote_counter = Counter(votes)
        max_votes = max(vote_counter.values())
        top_maps = [index for index, count in vote_counter.items() if count == max_votes]
        winning_index = random.choice(top_maps) if len(top_maps) > 1 else top_maps[0]
        self.final_map = self.selected_maps[winning_index]
        self.animation_timer = 60

    def get_final_map(self):
        return self.final_map

    def update_animations(self):
        # Update animation timers
        if self.animation_timer > 0:
            self.animation_timer -= 1

        if self.transition_effect > 0:
            self.transition_effect = max(0.0, self.transition_effect - 0.02)

        for player in self.players.values():
            if player.vote_flash_timer > 0:
                player.vote_flash_timer -= 1

    def draw_player_indicators(self, screen):
        # Draw player selection indicators
        for player_id in [1, 2]:
            if self.players[player_id].selection_index >= len(self.selected_maps):
                continue

            selection_idx = self.players[player_id].selection_index
            map_count = len(self.selected_maps)

            # Calculate x position based on the card position
            total_width = (config.SEL_CARD_WIDTH * map_count) + (config.SEL_CARD_SPACING * (map_count - 1))
            start_x = (config.SCREEN_WIDTH - total_width) // 2
            x = start_x + (config.SEL_CARD_WIDTH + config.SEL_CARD_SPACING) * selection_idx + config.SEL_CARD_WIDTH // 2

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
        # Calculate total width of all cards + spacing
        total_width = (config.SEL_CARD_WIDTH * map_count) + (config.SEL_CARD_SPACING * (map_count - 1))
        start_x = (config.SCREEN_WIDTH - total_width) // 2

        for i, (name, map_data) in enumerate(self.selected_maps):
            # Calculate position with spacing
            x = start_x + (config.SEL_CARD_WIDTH + config.SEL_CARD_SPACING) * i
            y = config.SCREEN_HEIGHT // 2 - config.SEL_CARD_HEIGHT // 2

            # Apply entrance animation
            if self.animation_timer > 0:
                offset = (30 - min(30, self.animation_timer)) / 30
                y = y + (1 - offset) * 300

            # Create card rect
            card_rect = pygame.Rect(x, y, config.SEL_CARD_WIDTH, config.SEL_CARD_HEIGHT)

            # Determine if this card is selected by either player
            p1_selected = self.players[1].selection_index == i
            p2_selected = self.players[2].selection_index == i
            p1_voted = self.players[1].vote_index == i
            p2_voted = self.players[2].vote_index == i

            # Draw card background with rounded corners (radius of 15)
            self.draw_rounded_rect(screen, config.SELECTOR_COLORS['map_bg'], card_rect, 15)

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
            screen.blit(name_text, (x + config.SEL_CARD_WIDTH // 2 - name_text.get_width() // 2, y + 20))

            # Draw vote indicators
            vote_y = y + config.SEL_CARD_HEIGHT - 40

            if p1_voted:
                flash_effect = self.players[1].vote_flash_timer > 0 and self.players[1].vote_flash_timer % 10 < 5
                vote_color = (255, 255, 255) if flash_effect else config.SELECTOR_COLORS['p1']
                vote_text = self.info_font.render("P1 Vote", True, vote_color)
                screen.blit(vote_text, (x + 20, vote_y))

            if p2_voted:
                flash_effect = self.players[2].vote_flash_timer > 0 and self.players[2].vote_flash_timer % 10 < 5
                vote_color = (255, 255, 255) if flash_effect else config.SELECTOR_COLORS['p2']
                vote_text = self.info_font.render("P2 Vote", True, vote_color)
                screen.blit(vote_text, (x + config.SEL_CARD_WIDTH - 20 - vote_text.get_width(), vote_y))



    def draw_instructions(self, screen):
        # Player 1 instructions
        if self.players[1].vote_index is None:
            p1_text = "Player 1: ← → to move, ENTER to vote"
        else:
            p1_text = "Player 1: Vote confirmed!"

        p1_instr = self.instruction_font.render(p1_text, True, config.SELECTOR_COLORS['p1'])
        screen.blit(p1_instr, (50, config.SCREEN_HEIGHT - 80))

        # Player 2 instructions
        if self.players[2].vote_index is None:
            p2_text = "Player 2: A D to move, RIGHT SHIFT to vote"
        else:
            p2_text = "Player 2: Vote confirmed!"

        p2_instr = self.instruction_font.render(p2_text, True, config.SELECTOR_COLORS['p2'])
        screen.blit(p2_instr, (config.SCREEN_WIDTH - 50 - p2_instr.get_width(), config.SCREEN_HEIGHT - 80))

    def render(self, screen):
        if self.final_map:
            map_name, map_data = self.final_map
        
            # Try to load preview image
            try:
                preview_image = pygame.image.load(
                    os.path.join("assets", "map_previews", f"{map_name.lower().replace(' ', '_')}_preview.png")
                )
                preview_image = pygame.transform.scale(preview_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                screen.blit(preview_image, (0, 0))
            except:
                screen.fill((0, 0, 0))
        
            # Fade-in overlay
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, min(255, self.animation_timer * 6)))
            screen.blit(overlay, (0, 0))
        
            # Text setup
            map_name_text = self.title_font.render(f"{map_name}", True, (0, 255, 255))
            text_x = config.SCREEN_WIDTH // 2 - map_name_text.get_width() // 2
            text_y = config.SCREEN_HEIGHT // 2 - 70
        
            # Glowing box around text
            glow_surface = pygame.Surface((map_name_text.get_width() + 60, map_name_text.get_height() + 40), pygame.SRCALPHA)
            glow_rect = glow_surface.get_rect(center=(config.SCREEN_WIDTH // 2, text_y + map_name_text.get_height() // 2 + 10))
            pygame.draw.rect(glow_surface, (0, 180, 255, 100), glow_surface.get_rect(), border_radius=20)
            screen.blit(glow_surface, glow_rect.topleft)
        
            # Dark rounded background box
            box_width = map_name_text.get_width() + 100
            box_height = map_name_text.get_height() + 130
            box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(box_surface, (15, 15, 30, 240), box_surface.get_rect(), border_radius=20)
            screen.blit(box_surface, (config.SCREEN_WIDTH // 2 - box_width // 2, text_y - 40))
        
            # Final glowing map name
            screen.blit(map_name_text, (text_x, text_y))
        
            # Subtext
            selected_label = self.info_font.render("Map Selected!", True, (200, 200, 200))
            screen.blit(selected_label, (
                config.SCREEN_WIDTH // 2 - selected_label.get_width() // 2,
                text_y + map_name_text.get_height() + 10
            ))
        
            start_text = self.info_font.render("Press SPACE to start", True, (255, 255, 0))
            screen.blit(start_text, (
            config.SCREEN_WIDTH // 2 - start_text.get_width() // 2, text_y + map_name_text.get_height() + 50))
        else:
            # Voting screen fallback
            screen.blit(self.bg_image, (0, 0))
            title = self.title_font.render("SELECT YOUR BATTLEFIELD", True, config.SELECTOR_COLORS['title'])
            screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
            self.draw_map_cards(screen)
            self.draw_player_indicators(screen)
            self.draw_instructions(screen)
        
        # Fade transition
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
                if self.players[1].vote_index is None:
                    self.confirm_vote(1)

            # Player 2: A / D to move, RSHIFT to confirm
            elif event.key == pygame.K_a:
                self.move_selection(2, -1)
            elif event.key == pygame.K_d:
                self.move_selection(2, 1)
            elif event.key == pygame.K_RSHIFT:
                if self.players[2].vote_index is None:
                    self.confirm_vote(2)



            if event.key == pygame.K_SPACE and self.final_map:
                self.exit_state()
                map_name = self.final_map[0]
                selected_map = self.final_map[1]
                self.state_manager.change_state("TestField", selected_map, map_name)
