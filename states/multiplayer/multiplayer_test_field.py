import random
import pygame
import copy
import config
import time

from typing import Dict,Tuple
from game_objects.multiplayer.multiplayer_power_up import PowerUp
from states.general.state import State
from game_objects.multiplayer.multiplayer_player import Player
from managers.music_manager import MusicManager
from managers.network_manager import NetworkManager
from managers.state_manager import StateManager
from maps.test_field_map import all_maps
from image_loader import load_images, load_hat_images
from game_objects.general.bomb import Bomb
from states.multiplayer.multiplayer_lobby import PlayerData

class MultiplayerTestField(State):
    def __init__(self, game, selected_map, network_manager: NetworkManager, players_list: Dict[str, PlayerData], player_name: str):
        super().__init__(game)
        
        self.network_manager: NetworkManager  = network_manager
        self.players_list = players_list
        self.player_name: str = player_name
        
        player = players_list.get(player_name)
        if player is None:
            raise Exception(f'player_name: {player_name} not found in player_list: {players_list}')
        
        self.my_player: PlayerData = player
        self.state_manager = StateManager(self.game)
        
        # Get map name from selected_map if it's a tuple, otherwise use as is
        if isinstance(selected_map, tuple):
            self.map_name = selected_map[0]
            self.tile_map = copy.deepcopy(selected_map[1])
        else:
            self.map_name = selected_map
            self.tile_map = copy.deepcopy(all_maps[selected_map])
        
        pygame.display.set_caption(f"BomberMan: {self.map_name} User: {self.player_name}")
        
        # Music manager
        self.music_manager = MusicManager()

        # Sprite groups
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Hidden power-ups map - stores which bricks have power-ups underneath
        self.hidden_powerups : Dict[Tuple[int,int], str] = {}
        # Load images
        self.images = load_images()
        hats = [player.final_hat for player in self.players_list.values()]
        self.hat_images = load_hat_images(hats)
        # Feedback message for power-ups
        self.powerup_message = ""
        self.message_timer = 0

        self.players: Dict[str,Player] = {}
        
        if self.my_player.is_host:
            # Players: dict player_name -> Player object
            for player in self.players_list.values():
                spawn = "spawn1" if player.name == self.player_name else "spawn4"
                self.players[player.name] = Player(spawn, self, player.name, player.final_color, player.final_hat)
            self.send_player_list()
            self.place_hidden_powerups()

    # ---------------- NETWORK ----------------
    def handle_network_packets(self):
        poll_data = self.network_manager.poll()
        if poll_data:
            self.handle_packet(poll_data)

    def handle_packet(self, poll_data):
        packet, addr = poll_data

        if not packet.get('scope') == 'MultiplayerTestField':
            return
        
        packet_type = packet.get('type')
        packet_data = packet.get('data')

        if not packet_type or not packet_data:
            return
        
        if packet_type == 'PLAYER_LIST':
            self._handle_player_list_packet(packet_data, addr)
        elif packet_type == "PLAYER_UPDATE":
            self._handle_player_update_packet(packet_data, addr)
        elif packet_type == 'BOMB_UPDATE':
            self._handle_bomb_update_packet(packet_data, addr)
        elif packet_type == 'POWERUP_UPDATE':
            self._handle_powerup_update_packet(packet_data, addr)

    def _handle_player_list_packet(self, packet_data, addr):
        """Receive initial player list"""
        for player_name, spawn in packet_data.get('list').items():
            if player_name not in self.players:
                player_color = self.players_list[player_name].final_color
                player_hat = self.players_list[player_name].final_hat
                self.players[player_name] = Player(spawn, self, player_name, player_color, player_hat)

    def _handle_player_update_packet(self, packet_data, addr):
        """Update player position"""
        player_name = packet_data.get('player_name')
        x = packet_data.get('x')
        y = packet_data.get('y')
        if player_name in self.players and player_name != self.player_name:
            self.players[player_name].rect.topleft = (x, y)

    def _handle_bomb_update_packet(self, packet_data, addr):
        """Receive bomb placement from other player"""
        player_name = packet_data.get('player_name')
        if player_name in self.players:
            Bomb(self.players.get(player_name), self.bomb_group, self.explosion_group, self)

    def _handle_powerup_update_packet(self, packet_data, addr):
        """Receive powerup spawn from other player"""
        x, y = map(int, packet_data.get('pos').split(','))
        powerup_type = packet_data.get('powerup_type')
        powerup = PowerUp(int(x), int(y), powerup_type)
        powerup.reveal()
        self.powerup_group.add(powerup)
 
    def send_player_list(self):
        indexes = {key: ('spawn1' if key == self.player_name else 'spawn4') for key in self.players.keys()}
        packet_data = {'list': indexes}
        self.send_packet('PLAYER_LIST', packet_data)

    def send_packet(self, packet_type, packet_data):
        """Broadcast packet to all other players"""
        scope = 'MultiplayerTestField'
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            self.network_manager.send_packet(player.addr, packet_type, packet_data, scope)
    # ---------------- Input ----------------
    def handle_events(self, event):
        player = self.players.get(self.player_name)
        if not player:
            return
        elif event.type == pygame.KEYDOWN:
            if event.key in player.move_keys and event.key not in player.held_down_keys:
                player.held_down_keys.append(event.key)
        elif event.type == pygame.KEYUP:
            if event.key in player.held_down_keys:
                player.held_down_keys.remove(event.key)

    # ---------------- Update ----------------
    def update(self):
        now = pygame.time.get_ticks()

        self.handle_network_packets()
        # Move local player based on held keys
        if self.players:
            local_player = self.players.get(self.player_name)
            if not local_player:
                return
            local_player.moving = False
            local_player.handle_queued_keys(now)
            local_player.update_powerups()

        if self.powerup_group:
            self.check_powerup_collisions()
        if self.explosion_group:
            self.handle_explosions()
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
                
                # Send the powerup to other players
                packet_data = {
                    'pos': f"{x},{y}",
                    'powerup_type': powerup_type
                }
                self.send_packet('POWERUP_UPDATE', packet_data)
                
            self.hidden_powerups.pop((x, y), None)
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
            self.hidden_powerups[(x,y)] = powerup_type

    def check_powerup_collisions(self):
        if self.powerup_group is None:
            return
        # Only collect visible (not hidden) power-ups
        visible_powerups = [p for p in self.powerup_group.sprites() if not p.hidden]

        for powerup in visible_powerups:
            for player_obj in self.players.values():
                if pygame.sprite.collide_rect(player_obj, powerup):
                    self.powerup_message = powerup.apply_effect(player_obj)
                    self.message_timer = pygame.time.get_ticks()
                    self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                    powerup.kill()  # Remove from sprite group

    def draw_active_powerups(self, screen):
        powerups_texts = []

        local_player = self.players.get(self.player_name)
        if local_player:
            for powerup, expire_time in local_player.active_powerups.items():
                remaining = round(expire_time - time.time(), 2)
                if remaining > 0:
                    if powerup == "shield_powerup":
                        powerups_texts.append(f"Shield: {remaining}s")
                    elif powerup == 'freeze_powerup':
                        powerups_texts.append(f'Freeze: {remaining}s')

        # Display power-ups
        y_offset = 40
        for text in powerups_texts:
            powerup_text = self.game.font.render(text, True, config.COLOR_BLACK)
            screen.blit(powerup_text, (10, y_offset))
            y_offset += 20

    def handle_explosions(self):
        if not self.explosion_group:
            return
        for hit_player_name, player_obj in list(self.players.items()):
            if player_obj.check_hit() and player_obj.get_health() <= 0:
                self.exit_state()
                winner = [player_name for player_name in list(self.players.keys()) if hit_player_name != player_name][0]
                self.state_manager.change_state("MultiplayerGameOver", winner, self.map_name, self.network_manager)
            
    # ---------------- Render ---------------
    def draw_menu(self, screen):
        num_players = len(self.players)
        if num_players == 0:
            return
        
        # Place players on edges (left and right)
        positions = [0, config.SCREEN_WIDTH - 150]
        
        for index, (name, player) in enumerate(self.players.items()):
            x_base = positions[index]
            
            # Heart icon
            screen.blit(self.images['heart_image'], (x_base, 5))
            
            # Lives
            lives_text = self.game.font.render(f"x {player.get_health()}", True, config.COLOR_BLACK)
            screen.blit(lives_text, (x_base + 30, 5))
            
            # Bomb icon
            screen.blit(self.images['bomb_icon'], (x_base + 80, 5))
            
            # Bomb count
            bombs_text = self.game.font.render(f"x {player.get_max_bombs()}", True, config.COLOR_BLACK)
            screen.blit(bombs_text, (x_base + 110, 5))
        
        # Display power-up message in middle
        if self.powerup_message:
            message_text = self.game.font.render(self.powerup_message, True, config.COLOR_BLACK)
            screen.blit(message_text, (config.SCREEN_WIDTH // 2 - message_text.get_width() // 2, 5))

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
    
    def _draw_player_hat(self, screen: pygame.Surface, player: Player) -> None:
        if not player.has_hat:
            return
        hat_name = player.get_player_hat()
        hat_image = self.hat_images[hat_name]
        
        # Get the current player animation to calculate offset for drawing hat
        anim_offsets = config.HAT_ANIM_OFFSETS.get(player.current_animation, [0, 0, 0])
        frame_index = player.current_frame_index % len(anim_offsets)
        anim_offset_y = anim_offsets[frame_index]
        
        going_right = pygame.K_d in player.held_down_keys
        
        # Applying the offset to player rect
        ox, oy = config.GAME_HAT_OFFSETS.get(hat_name, (0, 0))
        hx = player.rect.x + ox
        hy = player.rect.y + oy + anim_offset_y
        hat_to_draw = hat_image if not going_right else pygame.transform.flip(hat_image, True, False)
        
        screen.blit(hat_to_draw, (hx, hy))
    
    def _draw_players(self, screen: pygame.Surface) -> None:
        if not self.players:
            return
        for player in self.players.values():
            player.update_animation()
            self._draw_player_hat(screen, player)
            screen.blit(player.image, player.rect)

    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        self.draw_grid(screen)
        self.draw_walls(screen)
        self.draw_menu(screen)

        self._draw_players(screen)

        # Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # Draw visible power-ups
        self.powerup_group.draw(screen)

        # Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)


