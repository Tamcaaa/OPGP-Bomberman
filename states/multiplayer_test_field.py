import random
import pygame
import json
import copy
import config
import time

from power_up import PowerUp
from states.state import State
from player import Player
from managers.music_manager import MusicManager
from maps.test_field_map import all_maps
from image_loader import load_images
from bomb import Bomb

class MultiplayerTestField(State):
    def __init__(self, game, multiplayer_lobby, map_name):
        super().__init__(game)

        self.lobby = multiplayer_lobby
        pygame.display.set_caption(f"BomberMan: {map_name} User: {self.lobby.player_name}")
        self.map_name = map_name
        self.socket = self.lobby.socket
        
        # Music manager
        self.music_manager = MusicManager()

        # Load map
        self.tile_map = copy.deepcopy(all_maps[map_name])

        # Sprite groups
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Hidden power-ups map - stores which bricks have power-ups underneath
        self.hidden_powerups = {}  # Format: {(x, y): powerup_type}
        self.place_hidden_powerups()

        # Load images
        self.images = load_images()

        # Feedback message for power-ups
        self.powerup_message = ""
        self.message_timer = 0

        self.players = {}
        self.player_username = self.lobby.player_name

        # Players: dict player_name -> Player object
        if self.lobby.is_host:
            self.players = {}
            for player_name, _ in self.lobby.players:
                spawn = "spawn1" if player_name == self.player_username else "spawn4"
                self.players[player_name] = Player(1 if spawn == "spawn1" else 2, spawn, self,username=player_name)
            self.send_player_list()


    # ---------------- Network ----------------
    def handle_network_packets(self):
        try:
            packet, _ = self.socket.recvfrom(1024)
            data = json.loads(packet.decode("utf-8"))
            if data.get("type") == "PLAYER_UPDATE":
                player_username = data["player_username"]
                x = data["x"]
                y = data["y"]
                if player_username in self.players and player_username != self.player_username:
                    self.players[player_username].rect.topleft = (x, y)
            elif data.get('type') == 'PLAYER_LIST':
                for player_name, spawn in data['list'].items():
                    self.players[player_name] = Player(1 if player_name == self.player_username else 2,spawn, self,username=player_name)
            elif data.get('type') == 'BOMB_UPDATE':
                player_username = data['player_username']
                Bomb(self.players[player_username], self.bomb_group, self.explosion_group,self)

        except (BlockingIOError,TimeoutError) as e:
            # No data received
            pass

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
                if name != self.player_username:
                    self.socket.sendto(message, addr)

    def send_bomb_placement(self, bomb_packet):
        message = json.dumps(bomb_packet).encode("utf-8")
        for name, addr in self.lobby.players:
            if name != self.player_username:
                self.socket.sendto(message, addr)
    def send_packet(self, packet):
        message = json.dumps(packet).encode("utf-8")
        for name, addr in self.lobby.players:
            if name != self.player_username:
                self.socket.sendto(message, addr)
    # ---------------- Input ----------------
    def handle_events(self, event):
        player = self.players[self.player_username]
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
        now = pygame.time.get_ticks()
        # Update network first
        self.handle_network_packets()
        # Move local player based on held keys
        if self.players:
            local_player = self.players[self.player_username]
            local_player.moving = False
            local_player.handle_queued_keys(now)
            # Powerup updates
            self.check_powerup_collisions()
            local_player.update_powerups()
                # Clear power-up message after 3 seconds
        if self.message_timer > 0 and now - self.message_timer > 1500:
            self.powerup_message = ""
            self.message_timer = 0
    # --------------- Game Logic ----------------
    def destroy_tile(self, x, y):
        # Only handle brick tiles (2)
        if self.tile_map[y][x] == 2:
            # Check if there's a power-up hidden under this brick
            if (x, y) in self.hidden_powerups:
                powerup_type = self.hidden_powerups[(x, y)]
                powerup = PowerUp(x, y, powerup_type)
                powerup.reveal()
                self.powerup_group.add(powerup)
                del self.hidden_powerups[(x, y)]

            # Update the map (brick is destroyed)
            self.tile_map[y][x] = 0

    def place_hidden_powerups(self):
        brick_positions = []

        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                if self.tile_map[y][x] == 2:
                    brick_positions.append((x, y,))

        # Determine how many power-ups to place
        num_powerups = int(len(brick_positions) * config.POWERUP_SPAWNING_RATE)

        # Randomly select bricks to hide power-ups under
        selected_bricks = random.sample(brick_positions, min(num_powerups, len(brick_positions)))

        # Place power-ups under selected bricks
        for x, y in selected_bricks:
            powerup_type = random.choice(config.POWERUP_TYPES)
            self.hidden_powerups[(x, y)] = powerup_type  # Only store type here
    
    def check_powerup_collisions(self):
        if self.powerup_group is None:
            return
        # Only collect visible (not hidden) power-ups
        visible_powerups = [p for p in self.powerup_group.sprites() if not p.hidden]

        for powerup in visible_powerups:
            if pygame.sprite.collide_rect(self.players[self.player_username], powerup):
                self.powerup_message = powerup.apply_effect(self.players[self.player_username])
                self.message_timer = pygame.time.get_ticks()
                self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                powerup.kill()  # Remove from sprite group

    def draw_active_powerups(self, screen):
        powerups_text = []

        for powerup, expire_time in self.player_username.active_powerups.items():
            remaining = round(expire_time - time.time(), 2)
            if remaining > 0:
                if powerup == "shield_powerup":
                    powerups_text.append(f"Shield: {remaining}s")
                elif powerup == 'freeze_powerup':
                    powerups_text.append(f'Freeze: {remaining}s')

        # Display Player 1 power-ups
        y_offset = 40
        for text in powerups_text:
            powerup_text = self.game.font.render(text, True, config.COLOR_BLACK)
            screen.blit(powerup_text, (10, y_offset))
            y_offset += 20

    
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
        
        #self.draw_active_powerups(screen)

        # Display power-up message if active
        if self.powerup_message:
            message_text = self.game.font.render(self.powerup_message, True, config.COLOR_BLACK)
            screen.blit(message_text, (config.SCREEN_WIDTH // 2 - message_text.get_width() // 2, 10))

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

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎮 Draw visible power-ups
        self.powerup_group.draw(screen)

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)


