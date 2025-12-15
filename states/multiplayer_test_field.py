from operator import index

import pygame
import json
import copy
import time

from pyexpat.errors import messages

from states.state import State
from player import Player
from managers.music_manager import MusicManager
from maps.test_field_map import all_maps
import config
from image_loader import load_images

class MultiplayerTestField(State):
    def __init__(self, game, multiplayer_lobby, map_name):
        super().__init__(game)
        pygame.display.set_caption(f"BomberMan: {map_name}")

        self.lobby = multiplayer_lobby
        self.map_name = map_name
        self.socket = self.lobby.socket

        # Load map
        self.tile_map = copy.deepcopy(all_maps[map_name])

        # Sprite groups
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Load images
        self.images = load_images()

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
    # ---------------- Render ---------------
    def draw_menu(self, screen):
        num_players = len(self.players)
        if num_players == 0:
            return
        spacing = config.SCREEN_WIDTH // num_players
        for index, (name, player) in enumerate(self.players.items()):
            x_base = index * spacing
            # Heart
            screen.blit(self.images['heart_image'], (x_base, 0))
            # Lives
            lives_text = self.game.font.render(f"x {player.get_health()}", True, config.COLOR_BLACK)
            screen.blit(lives_text, (x_base + config.GRID_SIZE, 10))
            # Bomb icon
            screen.blit(self.images['bomb_icon'], (x_base + config.GRID_SIZE * 2, 0))
            # Bomb count
            bombs_text = self.game.font.render(f"x {player.get_max_bombs()}", True, config.COLOR_BLACK)
            screen.blit(bombs_text, (x_base + config.GRID_SIZE * 3, 10))

    def draw_grid(self, screen):
        if self.map_name == "Crystal Caves":
            screen.blit(self.images['cave_bg'], (0, 0))
            pass
        if self.map_name == "Classic":
            screen.blit(self.images['grass_bg'], (0, 0))
            pass
        if self.map_name == "Desert Maze":
            screen.blit(self.images['sand_bg'], (0, 0))
            pass
        if self.map_name == "Ancient Ruins":
            screen.blit(self.images['ruins_bg'], (0, 0))
            pass
        if self.map_name == "Urban Assault":
            screen.blit(self.images['urban_bg'], (0, 0))
            pass
        else:
            for line in range((config.SCREEN_WIDTH // config.GRID_SIZE) + 1):
                pygame.draw.line(screen, config.COLOR_BLACK, (line * config.GRID_SIZE, 30),
                                 (line * config.GRID_SIZE, config.SCREEN_HEIGHT))
            for line in range((config.SCREEN_HEIGHT // config.GRID_SIZE) - 1):
                pygame.draw.line(screen, config.COLOR_BLACK, (0, line * config.GRID_SIZE + 30),
                                 (config.SCREEN_WIDTH, line * config.GRID_SIZE + 30))
    def draw_walls(self, screen):
            for row_index, row in enumerate(self.tile_map):
                for col_index, tile in enumerate(row):
                    x = col_index * config.GRID_SIZE
                    y = row_index * config.GRID_SIZE
                    if tile in [0, 4, 5]:  # Empty space (no wall)
                        if self.map_name not in ["Crystal Caves", "Desert Maze", "Classic", "Ancient Ruins","Urban Assault"]:  #  Only draw green tiles on other maps
                            rect = pygame.Rect(x, y, config.GRID_SIZE, config.GRID_SIZE)
                            color = config.COLOR_DARK_GREEN if (col_index + row_index) % 2 == 0 else config.COLOR_LIGHT_GREEN
                            pygame.draw.rect(screen, color, rect)
                        
                    elif tile == 1:  # Unbreakable wall
                        if self.map_name == "Crystal Caves":
                            screen.blit(self.images['unbreakable_stone'], (x, y))
                        elif self.map_name in ["Classic", "Desert Maze"]:
                            screen.blit(self.images['unbreakable_box'], (x, y))
                        elif self.map_name == "Ancient Ruins":
                            screen.blit(self.images['unbreakable_rock'], (x, y))
                        else:
                            screen.blit(self.images['unbreakable_wall'], (x, y))
                    elif tile == 2:  # Breakable wall
                        if self.map_name == "Desert Maze":
                            screen.blit(self.images['breakable_cactus'], (x, y))
                        elif self.map_name == "Classic":
                            screen.blit(self.images['breakable_bush'], (x, y))
                        elif self.map_name == "Crystal Caves":
                            screen.blit(self.images['breakable_diamond'], (x, y))
                        elif self.map_name == "Ancient Ruins":
                            screen.blit(self.images['breakable_rock'], (x, y))
                        else:
                            screen.blit(self.images['breakable_wall'], (x, y))
                    if tile == 4:  # Blue cave
                        screen.blit(self.images['blue_cave'], (x, y))
                    if tile == 5:  # Red cave
                        screen.blit(self.images['red_cave'], (x, y))
                    elif tile == config.TRAP:  # Poklop
                        screen.blit(self.images['trap_image'], (x, y))


    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        self.draw_grid(screen)
        self.draw_walls(screen)
        self.draw_menu(screen)

        # Draw players
        if self.players:
            for player in self.players.values():
                player.update_animation()
                screen.blit(player.image, player.rect)


