import pygame
import os
import socket
import random
import config
from states.state import State
from maps.test_field_map import all_maps


class MultiplayerMapSelector(State):
    def __init__(self, game, multiplayer_lobby):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Map Selector")
        self.bg_image = pygame.image.load(os.path.join("assets", "bg.png"))

        self.lobby = multiplayer_lobby  # Keep reference to lobby for players and socket

        self.selected_maps = []
        self.all_maps = all_maps

        # Fonts (using enhanced fonts like local selector)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.map_font = pygame.font.SysFont('Arial', 28)
        self.info_font = pygame.font.SysFont('Arial', 22)
        self.font = pygame.font.Font(None, config.FONT_SIZE)  # fallback for buttons, etc.

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
                self.lobby.socket.sendto(message.encode('utf-8'), addr)

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
        if self.back_button.is_clicked():
            self.lobby.state_manager.change_state("MultiplayerLobby")

        if self.lobby.is_host:
            if self.start_button.is_clicked() and self.selected_map:
                # Broadcast state change to start game
                self.lobby.broadcast_state_change("MultiplayerGame")
                self.lobby.state_manager.change_state("MultiplayerGame")

            # Check map selection clicks
            mouse_pos = pygame.mouse.get_pos()
            for i, map_name in enumerate(self.available_maps):
                rect = pygame.Rect(config.SCREEN_WIDTH // 2 - 100, 150 + i * 60, 200, 50)
                if rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                    self.selected_map = map_name
                    self.send_map_selection()

    def update(self):
        pass

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
        total_maps = len(self.available_maps)
        card_width = config.SEL_CARD_WIDTH
        card_height = config.SEL_CARD_HEIGHT
        spacing = config.SEL_CARD_SPACING
        total_width = (card_width * total_maps) + (spacing * (total_maps - 1))
        start_x = (config.SCREEN_WIDTH - total_width) // 2
        y = config.SCREEN_HEIGHT // 2 - card_height // 2

        for i, map_name in enumerate(self.available_maps):
            x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Card background
            bg_color = config.SELECTOR_COLORS['map_bg']
            self.draw_rounded_rect(screen, bg_color, card_rect, 15)

            # Border color: highlight selected map
            border_color = config.SELECTOR_COLORS['map_border']
            border_width = 3
            if map_name == self.selected_map:
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

        # Draw buttons
        self.back_button.draw(screen)
        if self.lobby.is_host:
            self.start_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, config.BUTTON_HOVER_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, config.BUTTON_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
