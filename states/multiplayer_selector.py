import pygame
import os
import socket
import config
from states.state import State


class MultiplayerMapSelector(State):
    def __init__(self, game, multiplayer_lobby):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Map Selector")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "map_selector_bg.png"))

        self.lobby = multiplayer_lobby  # Keep reference to lobby for players and socket

        self.selected_map = None
        self.available_maps = ["Map1", "Map2", "Map3"]  # You can dynamically load this

        # Buttons
        self.back_button = Button(20, 20, config.BUTTON_WIDTH // 1.5, config.BUTTON_HEIGHT // 1.5, "Back")
        self.start_button = Button(config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
                                   config.SCREEN_HEIGHT - 120,
                                   config.BUTTON_WIDTH,
                                   config.BUTTON_HEIGHT,
                                   "Start Game")

        self.font = pygame.font.Font(None, config.FONT_SIZE)

    def send_map_selection(self):
        if self.lobby.is_host and self.selected_map:
            message = f"MAP_SELECTED:{self.selected_map}"
            for _, addr in self.lobby.players:
                self.lobby.socket.sendto(message.encode('utf-8'), addr)

    def listen_for_map_selection(self):
        try:
            message, _ = self.lobby.socket.recvfrom(1024)
            decoded = message.decode('utf-8')
            if decoded.startswith("MAP_SELECTED:"):
                _, map_name = decoded.split(":")
                self.selected_map = map_name
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
        self.listen_for_map_selection()

    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))
        self.game.draw_text(screen, "Select Map", config.COLOR_BLACK, config.SCREEN_WIDTH // 2, 60)

        # Draw available maps
        for i, map_name in enumerate(self.available_maps):
            y = 150 + i * 60
            color = config.COLOR_GREEN if map_name == self.selected_map else config.COLOR_BLACK
            pygame.draw.rect(screen, config.BUTTON_COLOR, (config.SCREEN_WIDTH // 2 - 100, y, 200, 50))
            text_surf = self.font.render(map_name, True, color)
            text_rect = text_surf.get_rect(center=(config.SCREEN_WIDTH // 2, y + 25))
            screen.blit(text_surf, text_rect)

        # Draw connected players
        y_start = 400
        for i, player in enumerate(self.lobby.players):
            player_name = player[0]
            text_surf = self.font.render(f"{i + 1}. {player_name}", True, config.TEXT_COLOR)
            screen.blit(text_surf, (50, y_start + i * 30))

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
