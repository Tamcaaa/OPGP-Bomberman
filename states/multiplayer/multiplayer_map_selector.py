import json
import pygame
import random
import config
import os
from typing import Dict
from states.general.state import State
from maps.test_field_map import all_maps
from collections import Counter
from managers.state_manager import StateManager
from managers.network_manager import NetworkManager

Addr = tuple[str, int]
Packet = Dict[str, any]

class MultiplayerMapSelector(State):
    def __init__(self, game, player_list, network_manger: NetworkManager, my_player_name: str):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Map Selector")
        self.bg_image = pygame.image.load(os.path.join("assets", "battlefield-bg.png"))
        self.battlefield_text = pygame.image.load(os.path.join("assets", "battlefield.png"))
        
        self.network_manager = network_manger
        self.players_list = player_list
        self.my_player = player_list.get(my_player_name)

        self.state_manager = StateManager(self.game)

        self.selected_maps = []
        self.final_map = None
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

        if self.my_player.is_host:
            self.select_random_maps()
            self.send_map_selection()

    # ==================== NETWORK ====================
    def select_random_maps(self):
        available_maps = list(self.all_maps.keys())
        count = min(3, len(available_maps))
        self.selected_maps = random.sample(available_maps, count)

    def send_map_selection(self):
        packet_type = 'MAP_SELECTION'
        packet_data = {'map_list': self.selected_maps}
        scope = 'MultiplayerMapSelector'
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            self.network_manager.send_packet(player.addr, packet_type, packet_data, scope)

    def send_packet(self, packet_type, packet_data):
        """Broadcast packet to all other players"""
        scope = 'MultiplayerMapSelector'
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            self.network_manager.send_packet(player.addr, packet_type, packet_data, scope)

    def handle_network_packets(self):
        poll_data = self.network_manager.poll()
        if poll_data:
            self.handle_packet(poll_data)

    def handle_packet(self, poll_data):
        packet, addr = poll_data

        if not packet.get('scope') == 'MultiplayerMapSelector':
            print(f'[SCOPE_ERROR] from MultiplayerMapSelector; packet:{packet} from {addr}')
            return
        packet_type = packet.get('type')
        packet_data = packet.get('data')

        if not packet_type or not packet_data:
            raise Exception(f'Invalid packet (data or type missing): packet:{packet} from {addr}')
        
        if packet_type == 'MOVE_SELECTION':
            self._handle_move_selection_packet(packet_data, addr)
        elif packet_type == 'MAP_SELECTION':
            self._handle_map_selection_packet(packet_data, addr)
        elif packet_type == 'CONFIRM_SELECTION':
            self._handle_confirm_selection_packet(packet_data, addr)
        elif packet_type == 'CANCEL_SELECTION':
            self._handle_cancel_selection_packet(packet_data, addr)
        elif packet_type == 'FINAL_MAP_SELECTION':
            self._handle_final_map_selection_packet(packet_data, addr)
        elif packet_type == 'STATE_CHANGE':
            self._handle_state_change_packet(packet_data, addr)

    def _handle_move_selection_packet(self, packet_data, addr):
        player_name = packet_data.get('player_name')
        new_index = packet_data.get('new_index')
        
        if not (player_name in self.players_list):
            print(f'[MOVE_SELECTION ERROR] Unknown player {player_name} from {addr}')
            return
        
        self.players_list[player_name].selection_index = new_index
        print(f'[MOVE_SELECTION] {player_name} moved to index {new_index} from {addr}')

    def _handle_map_selection_packet(self, packet_data, addr):
        map_list = packet_data.get('map_list')
        self.selected_maps = map_list
        print(f'[MAP_SELECTION] Received map list from {addr}')

    def _handle_confirm_selection_packet(self, packet_data, addr):
        player_name = packet_data.get('player_name')
        vote_index = packet_data.get('vote_index')
        
        if not (player_name in self.players_list):
            print(f'[CONFIRM_SELECTION ERROR] Unknown player {player_name} from {addr}')
            return
        
        self.players_list[player_name].vote_index = vote_index
        print(f'[CONFIRM_SELECTION] {player_name} voted for map index {vote_index} from {addr}')
        
        if all(player.vote_index is not None for player in self.players_list.values()) and self.my_player.is_host:
            self.determine_final_map()

    def _handle_cancel_selection_packet(self, packet_data, addr):
        player_name = packet_data.get('player_name')
        
        if not (player_name in self.players_list):
            print(f'[CANCEL_SELECTION ERROR] Unknown player {player_name} from {addr}')
            return
        
        self.players_list[player_name].vote_index = None
        print(f'[CANCEL_SELECTION] {player_name} canceled their vote from {addr}')

    def _handle_final_map_selection_packet(self, packet_data, addr):
        final_map = packet_data.get('final_map')
        self.final_map = final_map
        print(f'[FINAL_MAP_SELECTION] Final map selected: {final_map} from {addr}')

    def _handle_state_change_packet(self, packet_data, addr):
        new_state = packet_data.get('state')
        print(f'[STATE_CHANGE] Changing to state: {new_state} from {addr}')
        self.exit_state()
        self.state_manager.change_state(new_state, self.final_map, self.network_manager, self.players_list, self.my_player.name)

    def broadcast_state_change(self, new_state):
        packet_type = 'STATE_CHANGE'
        packet_data = {'state': new_state}
        scope = 'MultiplayerMapSelector'
        for player in self.players_list.values():
            self.network_manager.send_packet(player.addr, packet_type, packet_data, scope)

    # ==================== GAME LOGIC ====================
    def move_selection(self, player_name, direction):
        current = self.players_list.get(player_name).selection_index
        self.players_list.get(player_name).selection_index = (current + direction) % len(self.selected_maps)

        print(f"[MOVE] {player_name} moved from {current} to {self.players_list.get(player_name).selection_index}")

        packet_data = {
            'player_name': player_name,
            'new_index': self.players_list.get(player_name).selection_index
        }
        self.send_packet('MOVE_SELECTION', packet_data)

    def confirm_vote(self):
        player = self.players_list.get(self.my_player.name)
        player.vote_index = player.selection_index
        packet_data = {
            'player_name': self.my_player.name,
            'vote_index': player.vote_index
        }
        self.send_packet('CONFIRM_SELECTION', packet_data)
        if all(player.vote_index is not None for player in self.players_list.values()) and self.my_player.is_host:
            self.determine_final_map()

    def cancel_vote(self):
        player = self.players_list.get(self.my_player.name)
        player.vote_index = None
        packet_data = {'player_name': self.my_player.name}
        self.send_packet('CANCEL_SELECTION', packet_data)

    def determine_final_map(self):
        votes = [player.vote_index for player in self.players_list.values() if player.vote_index is not None]
        vote_counter = Counter(votes)
        max_votes = max(vote_counter.values())
        top_maps = [index for index, count in vote_counter.items() if count == max_votes]
        winning_index = random.choice(top_maps) if len(top_maps) > 1 else top_maps[0]
        self.final_map = self.selected_maps[winning_index]
        packet_data = {'final_map': self.final_map}
        self.send_packet('FINAL_MAP_SELECTION', packet_data)

    # ==================== INPUT ====================
    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            # If space is pressed and the final map is selected, exit the loop
            if self.final_map:
                if event.key == pygame.K_SPACE and self.my_player.is_host:
                    self.broadcast_state_change('MultiplayerTestField')
                    self.exit_state()
                    self.state_manager.change_state("MultiplayerTestField", self.final_map, self.network_manager, self.players_list, self.my_player.name)
            elif event.key == pygame.K_RETURN:
                if self.players_list.get(self.my_player.name).vote_index is None:
                    self.confirm_vote()
                else:
                    self.cancel_vote()
            elif self.players_list.get(self.my_player.name).vote_index is not None:
                return
            elif event.key == pygame.K_a:
                self.move_selection(self.my_player.name, -1)
            elif event.key == pygame.K_d:
                self.move_selection(self.my_player.name, 1)

    # ==================== UPDATE ====================
    def update(self):
        self.handle_network_packets()
        self.network_manager.update()

    # ==================== RENDERING ====================
    def draw_card(self, screen, i, map_name):
        """Draw a map card matching single-player style"""
        map_count = len(self.selected_maps)
        total_width = map_count * self.card_width + (map_count - 1) * self.card_spacing
        start_x = (config.SCREEN_WIDTH - total_width) // 2
        x = start_x + i * (self.card_width + self.card_spacing)
        y = config.SCREEN_HEIGHT // 2 - self.card_height // 2

        # Card background
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(screen, config.COLOR_BEIGE, rect, border_radius=self.card_radius)

        # Draw borders for each player's selection using their lobby color
        for player in self.players_list.values():
            if not (self.my_player == player) and player.selection_index == i:
                player_color = config.AVAILABLE_COLORS[player.color_index]
                pygame.draw.rect(screen, player_color, rect, 4, border_radius=self.card_radius)
        if self.my_player.selection_index == i:
            # Draw my_player border as last so the my_player color is on top 
            player_color = config.AVAILABLE_COLORS[self.my_player.color_index]
            pygame.draw.rect(screen, player_color, rect, 4, border_radius=self.card_radius)
        
        # Map name text
        text_surf = self.map_font.render(map_name, True, config.TEXT_COLOR)
        screen.blit(text_surf, (x + self.card_width // 2 - text_surf.get_width() // 2, y + 10))

        # Map preview if available
        try:
            preview_img = pygame.image.load(os.path.join("assets", "map_previews",f"{map_name.lower().replace(' ', '_')}_preview.png"))
            preview_img = pygame.transform.scale(preview_img, (self.card_width - 20, self.card_height - 50))
            screen.blit(preview_img, (x + 10, y + 40))
        except:
            pass

    @staticmethod
    def draw_rounded_rect(surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle"""
        rect = pygame.Rect(rect)
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)
        if border_width != 0:
            pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

    def draw_instructions(self, screen):
        # Player instructions - use player's color
        my_player = self.players_list.get(self.my_player.name)
        player_color = config.AVAILABLE_COLORS[my_player.color_index]
        
        if my_player.vote_index is None:
            instruction_text = "← → to move, ENTER to vote"
        else:
            instruction_text = "Vote confirmed! ENTER to cancel vote"

        instr_surf = self.info_font.render(instruction_text, True, player_color)
        screen.blit(instr_surf, (50, config.SCREEN_HEIGHT - 80))

    def draw_map_cards(self, screen):
        total_maps = len(self.selected_maps)
        card_width = config.SEL_CARD_WIDTH
        card_height = config.SEL_CARD_HEIGHT
        spacing = config.SEL_CARD_SPACING
        total_width = (card_width * total_maps) + (spacing * (total_maps - 1))
        start_x = (config.SCREEN_WIDTH - total_width) // 2
        y = config.SCREEN_HEIGHT // 2 - card_height // 2

        for i, map_name in enumerate(self.selected_maps):
            x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Card background
            bg_color = config.SELECTOR_COLORS['map_bg']
            self.draw_rounded_rect(screen, bg_color, card_rect, 15)

            # Border color: highlight selected map
            border_color = config.SELECTOR_COLORS['map_border']
            border_width = 3
            if map_name == self.final_map:
                border_color = config.COLOR_GREEN
                border_width = 5
            self.draw_rounded_rect(screen, border_color, card_rect, 15, border_width)

            # Map name text centered on card
            text_surf = self.map_font.render(map_name, True, config.SELECTOR_COLORS['text'])
            text_rect = text_surf.get_rect(center=card_rect.center)
            screen.blit(text_surf, text_rect)

        # Draw player names (with index) under each selected map
        name_offset_y = 20
        if len(self.selected_maps) > 2:
            player_stacks = {i: [] for i in range(len(self.selected_maps))}  # index -> list of (player_name)

            # Build stack lists for each map index
            for player in self.players_list.values():
                map_index = player.selection_index
                player_stacks[map_index].append(player.name)

            # Render stacked names under each map
            for map_index, player_list in player_stacks.items():
                x = start_x + map_index * (card_width + spacing)
                for stack_index, player_name in enumerate(player_list):
                    y_text = y + card_height + 10 + stack_index * name_offset_y
                    label = f"{stack_index + 1}. {player_name}"
                    name_surf = self.info_font.render(label, True, config.TEXT_COLOR if self.players_list.get(player_name).vote_index is None else config.COLOR_LIGHT_GREEN)
                    name_rect = name_surf.get_rect(center=(x + card_width // 2, y_text))
                    screen.blit(name_surf, name_rect)

    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Draw battlefield title
        screen.blit(self.battlefield_text, (config.SCREEN_WIDTH // 2 - self.battlefield_text.get_width() // 2, 40))

        if self.final_map:
            # Final map selection overlay
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))

            # Centered map name text
            text_surf = self.title_font.render(f"{self.final_map} Selected!", True, (0, 255, 255))
            screen.blit(text_surf,
                        (config.SCREEN_WIDTH // 2 - text_surf.get_width() // 2, config.SCREEN_HEIGHT // 2 - 50))

            if self.players_list.get(self.my_player.name).is_host:
                start_text = self.info_font.render("Press SPACE to start", True, (255, 255, 0))
                screen.blit(start_text,
                            (config.SCREEN_WIDTH // 2 - start_text.get_width() // 2, config.SCREEN_HEIGHT // 2 + 20))
            else:
                wait_text = self.info_font.render("Wait for Host to start", True, (255, 255, 0))
                screen.blit(wait_text,
                            (config.SCREEN_WIDTH // 2 - wait_text.get_width() // 2, config.SCREEN_HEIGHT // 2 + 20))
        else:
            # Draw map cards
            for i, map_name in enumerate(self.selected_maps):
                self.draw_card(screen, i, map_name)

            # Instructions 
            my_player = self.players_list.get(self.my_player.name)
            player_color = config.AVAILABLE_COLORS[my_player.color_index]
            
            if my_player.vote_index is None:
                instruction_text = "A D to move, ENTER to vote"
            else:
                instruction_text = "Vote confirmed!"

            instr_surf = self.info_font.render(instruction_text, True, player_color)
            screen.blit(instr_surf, (50, config.SCREEN_HEIGHT - 80))
