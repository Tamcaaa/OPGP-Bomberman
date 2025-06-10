import json
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
    vote_flash_timer: int = 0


class MultiplayerMapSelector(State):
    def __init__(self, game, multiplayer_lobby):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Map Selector")
        self.bg_image = pygame.image.load(os.path.join("assets", "bg.png"))

        self.lobby = multiplayer_lobby  # Keep reference to lobby for players and socket
        self.socket = self.lobby.socket

        self.players = {player: PlayerSelection() for player in self.lobby.players}
        print(self.players)

        self.state_manager = StateManager(self.game)

        self.selected_maps = []
        self.final_map = None
        self.all_maps = all_maps

        # Fonts
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.map_font = pygame.font.SysFont('Arial', 28)
        self.info_font = pygame.font.SysFont('Arial', 22)
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
        message = f"MAP_SELECTED:{self.selected_maps}"
        print(message)
        for _, addr in self.lobby.players:
            if addr[1] != 1111:
                self.socket.sendto(message.encode('utf-8'), addr)

    def move_selection(self, player_id, direction):
        current = self.players[player_id].selection_index
        self.players[player_id].selection_index = (current + direction) % len(self.selected_maps)

        # Send packet to server
        packet = {
            "type": "move_selection",
            "player_id": player_id,
            "new_index": self.players[player_id].selection_index
        }
        message = json.dumps(packet).encode('utf-8')
        self.socket.sendto(message, (self.lobby.host_ip,9999))  # self.server_address should be a (host, port) tuple

        # Optionally play sound locally
        # self.music_manager.play_sound("move_map_selector")")

    def handle_network_packets(self):
        try:
            message, _ = self.lobby.socket.recvfrom(1024)
            decoded = message.decode('utf-8')
            if decoded.startswith("MAP_SELECTED:"):
                # Format: MAP_SELECTED:<
                _, map_name = decoded.split(":")
                self.selected_maps = map_name
        except socket.timeout:
            pass

    def handle_events(self, event):
        pass

    def update(self):
        self.handle_network_packets()

    @staticmethod
    def draw_rounded_rect(surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle"""
        rect = pygame.Rect(rect)
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)
        if border_width != 0:
            pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

    def render(self, screen):
        # Background
        screen.blit(self.bg_image, (0, 0))

        # Title text
        title = self.title_font.render("SELECT YOUR BATTLEFIELD", True, config.SELECTOR_COLORS['title'])
        screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

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

        # Draw connected players list on left bottom
        y_start = config.SCREEN_HEIGHT - 150
        for i, player in enumerate(self.lobby.players):
            player_name = player[0]
            player_text = self.info_font.render(f"{i + 1}. {player_name}", True, config.TEXT_COLOR)
            screen.blit(player_text, (50, y_start + i * 30))
