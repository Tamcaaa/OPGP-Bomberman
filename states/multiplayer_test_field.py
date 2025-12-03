from operator import index

import pygame
import json
import copy
import time

from pyexpat.errors import messages

from states.state import State
from player import Player
from managers.music_manager import MusicManager
from maps.test_field_map import test_map
import config

class MultiplayerTestField(State):
    def __init__(self, game, multiplayer_lobby, map_name):
        super().__init__(game)
        pygame.display.set_caption(f"BomberMan: {map_name}")

        self.lobby = multiplayer_lobby
        self.map_name = map_name
        self.socket = self.lobby.socket

        # Load map
        self.tile_map = copy.deepcopy(test_map)

        # Sprite groups
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()


        self.players = {}
        self.player_name = self.lobby.player_name

        # Players: dict player_name -> Player object
        if self.lobby.is_host:
            self.players = {}
            for player_name, _ in self.lobby.players:
                spawn = "spawn1" if player_name == self.player_name else "spawn4"
                self.players[player_name] = Player(1 if spawn == "spawn1" else 2, spawn, self)
            self.send_player_list()


    # ---------------- Network ----------------
    def handle_network_packets(self):
        """Receive updates from network (other players)"""
        try:
            packet, _ = self.socket.recvfrom(1024)
            data = json.loads(packet.decode("utf-8"))
            if data.get("type") == "PLAYER_UPDATE":
                player_id = data["player_id"]
                x = data["x"]
                y = data["y"]
                if player_id in self.players and player_id != self.player_name:
                    self.players[player_id].rect.topleft = (x, y)
            elif data.get('type') == 'PLAYER_LIST':
                for player_name, spawn in data['list'].items():
                    self.players[player_name] = Player(1 if player_name == self.player_name else 2,spawn, self)
        except (BlockingIOError,TimeoutError) as e:
            # No data received
            pass

    def send_position(self):
        """Send local player position to host or broadcast"""
        player = self.players[self.player_name]
        packet = {
            "type": "PLAYER_UPDATE",
            "player_id": self.player_name,
            "x": player.rect.x,
            "y": player.rect.y
        }
        message = json.dumps(packet).encode("utf-8")

        if self.lobby.is_host:
            # Broadcast to all clients
            for name, addr in self.lobby.players:
                if name != self.player_name:
                    self.socket.sendto(message, addr)
        else:
            # Send only to host
            self.socket.sendto(message, (self.lobby.address_to_join, 9999))
    def send_player_list(self):
        indexes = {key:('spawn1' if key == 'Server Host' else 'spawn4') for key in self.players.keys()}
        packet = {
            'type': "PLAYER_LIST",
            'list': indexes
        }
        message = json.dumps(packet).encode("utf-8")
        if self.lobby.is_host:
            # Broadcast to all clients
            for name, addr in self.lobby.players:
                if name != self.player_name:
                    self.socket.sendto(message, addr)

    # ---------------- Input ----------------
    def handle_events(self, event):
        player = self.players[self.player_name]
        if event.type == pygame.KEYDOWN:
            if event.key in player.move_keys and event.key not in player.held_down_keys:
                player.held_down_keys.append(event.key)
            if event.key == pygame.K_p and self.lobby.is_host:
                self.game.state_manager.change_state("Pause", self.map_name, self.map_name)

        elif event.type == pygame.KEYUP:
            if event.key in player.held_down_keys:
                player.held_down_keys.remove(event.key)

    # ---------------- Update ----------------
    def update(self):
        # Update network first
        self.handle_network_packets()

        # Move local player based on held keys
        if self.players:
            local_player = self.players[self.player_name]
            now = pygame.time.get_ticks()
            local_player.handle_queued_keys(now)
            # Send updated position to host / broadcast
            self.send_position()

    # ---------------- Render ----------------
    def draw_grid(self,screen):
        for line in range((config.SCREEN_WIDTH // config.GRID_SIZE) + 1):
            pygame.draw.line(screen, config.COLOR_BLACK, (line * config.GRID_SIZE, 30),
                             (line * config.GRID_SIZE, config.SCREEN_HEIGHT))
        for line in range((config.SCREEN_HEIGHT // config.GRID_SIZE) - 1):
            pygame.draw.line(screen, config.COLOR_BLACK, (0, line * config.GRID_SIZE + 30),
                             (config.SCREEN_WIDTH, line * config.GRID_SIZE + 30))


    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        self.draw_grid(screen)
        # Draw players
        if self.players:
            for player in self.players.values():
                player.update_animation()
                screen.blit(player.image, player.rect)


