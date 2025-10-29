import ast
import json
import time

import pygame
import random

import config
import os
import socket
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


class MultiplayerMapSelector(State):
    def __init__(self, game, multiplayer_lobby):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Map Selector")
        self.bg_image = pygame.image.load(os.path.join("assets", "bg.png"))

        self.lobby = multiplayer_lobby  # Keep reference to lobby for players and socket
        self.socket = self.lobby.socket

        self.players = {player_name: PlayerSelection() for player_name, _ in self.lobby.players}

        self.state_manager = StateManager(self.game)

        self.selected_maps = []
        self.final_map = None
        self.all_maps = all_maps

        # Fonts
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.map_font = pygame.font.SysFont('Arial', 28)
        self.info_font = pygame.font.SysFont('Arial', 22)
        self.instruction_font = pygame.font.SysFont('Arial', 20)
        self.font = pygame.font.Font(None, config.FONT_SIZE)  # fallback for buttons

        # Animation variables
        self.animation_timer = 30
        self.transition_effect = 1.0

        self.player_name = self.lobby.player_name

        if self.lobby.is_host:
            self.select_random_maps()
            self.send_map_selection()

    def select_random_maps(self):
        available_maps = list(self.all_maps.keys())
        count = min(3, len(available_maps))
        self.selected_maps = random.sample(available_maps, count)

    def send_map_selection(self):
        packet_map_selection = {
            'type': 'MAP_SELECTION',
            'data': {'map_list': self.selected_maps},
        }
        for _, addr in self.lobby.players:
            if addr[1] != 1111:
                self.socket.sendto(json.dumps(packet_map_selection).encode('utf-8'), addr)

    def move_selection(self, player_name, direction):
        current = self.players[player_name].selection_index
        self.players[player_name].selection_index = (current + direction) % len(self.selected_maps)

        print(f"[MOVE] {player_name} moved from {current} to {self.players[player_name].selection_index}")

        packet = {
            "type": "MOVE_SELECTION",
            "player_id": player_name,
            "new_index": self.players[player_name].selection_index
        }

        message = json.dumps(packet).encode('utf-8')

        if self.lobby.is_host:
            # Broadcast to all clients
            for name, addr in self.lobby.players:
                if name != self.player_name:  # Don't send to self
                    self.socket.sendto(message, addr)
        else:
            # Clients only send to host
            self.socket.sendto(message, (self.lobby.address_to_join, 9999))

    def handle_network_packets(self):
        try:
            packet, _ = self.lobby.socket.recvfrom(1024)
            raw_data = packet.decode('utf-8')
            print(f"[NETWORK] Received packet: {raw_data}")
            packet = json.loads(raw_data)
            packet_type = packet.get('type')
            print(f"[NETWORK] Packet type: {packet_type}")

            if packet_type == 'MOVE_SELECTION':
                player_id = packet['player_id']
                new_index = packet['new_index']
                if player_id in self.players:
                    self.players[player_id].selection_index = new_index
                else:
                    print(f"[WARN] Unknown player in MOVE_SELECTION: {player_id}")

            elif packet_type == 'MAP_SELECTION':
                self.selected_maps = packet['data']['map_list']

            elif packet_type == 'CONFIRM_SELECTION':
                player_id = packet['player_id']
                vote_index = packet['vote_index']
                if player_id in self.players:
                    self.players[player_id].vote_index = vote_index
                    print(f"[VOTE] {player_id} voted for map index {vote_index}")
                    if all(p.vote_index is not None for p in
                           self.players.values()) and self.player_name == "Server Host":
                        self.determine_final_map()
                else:
                    print(f"[WARN] Unknown player in CONFIRM_SELECTION: {player_id}")
            elif packet_type == 'CANCEL_SELECTION':
                player_id = packet['player_id']
                if player_id in self.players:
                    self.players[player_id].vote_index = None
                    print(f"[VOTE] {player_id} canceled their vote")
                else:
                    print(f"[WARN] Unknown player in CANCEL_SELECTION: {player_id}")
            elif packet_type == 'FINAL_MAP_SELECTION':
                self.final_map = packet['final_map']



        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode failed: {e}")
        except socket.timeout:
            pass
        except Exception as e:
            print(f"[EXCEPTION] Network handler crashed: {e}")

    def confirm_vote(self):
        player = self.players[self.player_name]
        player.vote_index = player.selection_index
        packet = {
            "type": "CONFIRM_SELECTION",
            "player_id": self.player_name,
            "vote_index": player.vote_index
        }
        message = json.dumps(packet).encode("utf-8")
        for name, addr in self.lobby.players:
            if name != self.player_name:
                self.socket.sendto(message, addr)
        if all(p.vote_index is not None for p in self.players.values()) and self.player_name == "Server Host":
            self.determine_final_map()

    def determine_final_map(self):
        votes = [p.vote_index for p in self.players.values() if p.vote_index is not None]
        vote_counter = Counter(votes)
        max_votes = max(vote_counter.values())
        top_maps = [index for index, count in vote_counter.items() if count == max_votes]
        winning_index = random.choice(top_maps) if len(top_maps) > 1 else top_maps[0]
        self.final_map = self.selected_maps[winning_index]
        packet = {
            "type": "FINAL_MAP_SELECTION",
            "final_map": self.selected_maps[winning_index]
        }
        message = json.dumps(packet).encode("utf-8")
        for name, addr in self.lobby.players:
            if name != self.player_name:
                self.socket.sendto(message, addr)

    def cancel_vote(self):
        player = self.players[self.player_name]
        player.vote_index = None
        packet = {
            "type": "CANCEL_SELECTION",
            "player_id": self.player_name,
        }
        message = json.dumps(packet).encode("utf-8")
        for name, addr in self.lobby.players:
            if name != self.player_name:
                print(self.lobby.players)
                self.socket.sendto(message, addr)

    def broadcast_state_change(self, new_state):
        message = f"STATE_CHANGE:{new_state}".encode('utf-8')
        acknowledged_players = set()

        # Try to send up to 5 times, every 0.5 seconds
        for _ in range(5):
            for username, address in self.players:
                if address[1] == 1111:  # skip host
                    continue
                if address not in acknowledged_players:
                    self.socket.sendto(message, address)

            time.sleep(0.5)

            if len(acknowledged_players) == len(self.players) - 1:
                print("All clients acknowledged state change.")
                return True

        else:
            print("Not all clients acknowledged the state change.")
            return False

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            # If space is pressed and the final map is selected, exit the loop
            if self.lobby.is_host:
                if event.key == pygame.K_SPACE and self.final_map:
                    if self.broadcast_state_change('MultiplayerTestField'):
                        self.exit_state()
                        self.state_manager.change_state("MultiplayerTestField", self.lobby, self.final_map)
            if event.key == pygame.K_RETURN:
                if self.players[self.player_name].vote_index is None:
                    self.confirm_vote()
                else:
                    self.cancel_vote()
            elif self.players[self.player_name].vote_index is not None:
                return
            elif event.key == pygame.K_LEFT:
                self.move_selection(self.player_name, -1)
            elif event.key == pygame.K_RIGHT:
                self.move_selection(self.player_name, 1)

    def update(self):
        self.handle_network_packets()

    @staticmethod
    def draw_rounded_rect(surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle"""
        rect = pygame.Rect(rect)
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)
        if border_width != 0:
            pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

    def draw_instructions(self, screen):
        # Player instructions
        if self.players[self.player_name].vote_index is None:
            instruction_text = "← → to move, ENTER to vote"
        else:
            instruction_text = "Vote confirmed! ENTER to cancel vote"

        p1_instr = self.instruction_font.render(instruction_text, True, config.TEXT_COLOR)
        screen.blit(p1_instr, (50, config.SCREEN_HEIGHT - 80))

    def draw_map_cards(self, screen):
        # Draw map cards styled like local selector
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
            for player_name, sel in self.players.items():
                map_index = sel.selection_index
                player_stacks[map_index].append(player_name)

            # Render stacked names under each map
            for map_index, player_list in player_stacks.items():
                x = start_x + map_index * (card_width + spacing)
                for stack_index, player_name in enumerate(player_list):
                    y_text = y + card_height + 10 + stack_index * name_offset_y
                    label = f"{stack_index + 1}. {player_name}"
                    name_surf = self.info_font.render(label, True, config.TEXT_COLOR if self.players[
                                                                                            player_name].vote_index is None else
                    config.COLOR_LIGHT_GREEN)
                    name_rect = name_surf.get_rect(center=(x + card_width // 2, y_text))
                    screen.blit(name_surf, name_rect)

    def render(self, screen):
        if self.final_map:
            map_name = self.final_map
            try:
                preview_path = os.path.join("assets", "map_previews",
                                            f"{map_name.lower().replace(' ', '_')}_preview.png")

                preview_image = pygame.image.load(preview_path)
                preview_image = pygame.transform.scale(preview_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                screen.blit(preview_image, (0, 0))
            except (pygame.error, FileNotFoundError, AttributeError, TypeError, ValueError) as e:
                print(f"[{type(e).__name__}] Error loading or processing preview image: {e}")
                screen.fill((0, 0, 0))

            map_name_text = self.title_font.render(f"{map_name}", True, (0, 255, 255))
            text_x = config.SCREEN_WIDTH // 2 - map_name_text.get_width() // 2
            text_y = config.SCREEN_HEIGHT // 2 - 50

            announcement_bg = pygame.Surface((map_name_text.get_width() + 80, map_name_text.get_height() + 100),
                                             pygame.SRCALPHA)
            bg_rect = announcement_bg.get_rect()
            pygame.draw.rect(announcement_bg, (20, 20, 30, 230), bg_rect, border_radius=20)
            screen.blit(announcement_bg, (text_x - 40, text_y - 30))

            screen.blit(map_name_text, (text_x, text_y))

            selected_label = self.info_font.render("Selected Map", True, (200, 200, 200))
            screen.blit(selected_label,
                        (config.SCREEN_WIDTH // 2 - selected_label.get_width() // 2,
                         text_y + map_name_text.get_height() + 10))
            if self.lobby.is_host:
                start_text = self.info_font.render("Press SPACE to start the game", True, (255, 255, 0))
                screen.blit(start_text, (
                    config.SCREEN_WIDTH // 2 - start_text.get_width() // 2, text_y + map_name_text.get_height() + 50))
            else:
                wait_text = self.info_font.render("Wait for Host to start the game", True, (255, 255, 0))
                screen.blit(wait_text, (
                    config.SCREEN_WIDTH // 2 - wait_text.get_width() // 2, text_y + map_name_text.get_height() + 50))

        else:
            screen.blit(self.bg_image, (0, 0))

            # Title text
            title = self.title_font.render("SELECT YOUR BATTLEFIELD", True, config.SELECTOR_COLORS['title'])
            screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

            self.draw_instructions(screen)
            self.draw_map_cards(screen)
