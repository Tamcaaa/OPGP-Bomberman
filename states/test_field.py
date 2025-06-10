import pygame
import config
import copy
import time
import random

from states.state import State
from player import Player
from managers.music_manager import MusicManager
from power_up import PowerUp


class TestField(State):
    def __init__(self, game, selected_map, map_name, selected_skins=None):
        State.__init__(self, game)

        
        self.selected_map = selected_map
        self.map_name = map_name
        self.selected_skins = selected_skins or {}


        pygame.display.set_caption(f"BomberMan: {map_name}")
        self.game = game
        self.music_manager = MusicManager()

        self.keys_held = {pygame.K_s: False, pygame.K_d: False}

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()  # Group for power-ups

        # Hidden power-ups map - stores which bricks have power-ups underneath
        self.hidden_powerups = {}  # Format: {(x, y): powerup_type}

        self.player1 = Player(1, "spawn1", self, skin=self.selected_skins.get(1))
        self.player2 = Player(2, "spawn4", self, skin=self.selected_skins.get(2))
        self.players = [self.player1, self.player2]

        # Feedback message for power-ups
        self.powerup_message = ""
        self.message_timer = 0

        # Load images
        self.cave_bg = pygame.image.load("assets/cave-bg.png").convert_alpha()
        self.grass_bg = pygame.image.load("assets/grass-bg.png").convert_alpha()
        self.sand_bg = pygame.image.load("assets/sand-bg.png").convert_alpha()
        self.ruins_bg = pygame.image.load("assets/ruins_bg.png").convert_alpha()
        self.urban_bg = pygame.image.load("assets/urban_bg.png").convert_alpha()
        
        self.unbreakable_stone = pygame.image.load("assets/stone-black.png").convert_alpha()
        self.unbreakable_stone = pygame.transform.scale(self.unbreakable_stone, (30, 30))
        
        self.breakable_barrel = pygame.image.load("assets/environment/barrel.png").convert_alpha()
        self.breakable_barrel = pygame.transform.scale(self.breakable_barrel, (30, 30))
        
        self.breakable_bush = pygame.image.load("assets/environment/bush.png").convert_alpha()
        self.breakable_bush = pygame.transform.scale(self.breakable_bush, (30, 30))
        
        self.unbreakable_rock = pygame.image.load("assets/environment/black-block-rock.png").convert_alpha()
        self.unbreakable_rock = pygame.transform.scale(self.unbreakable_rock, (30, 30))
        self.breakable_rock = pygame.image.load("assets/environment/rock.png").convert_alpha()
        self.breakable_rock = pygame.transform.scale(self.breakable_rock, (30, 30))
        
        self.breakable_diamond = pygame.image.load("assets/environment/diamond.png").convert_alpha()
        self.breakable_diamond = pygame.transform.scale(self.breakable_diamond, (30, 30))
        
        self.breakable_cactus = pygame.image.load("assets/environment/cactus.png").convert_alpha()
        self.breakable_cactus = pygame.transform.scale(self.breakable_cactus, (30, 30))
        
        self.unbreakable_box = pygame.image.load("assets/environment/box.png").convert_alpha()
        self.unbreakable_box = pygame.transform.scale(self.unbreakable_box, (30, 30))
        
        self.heart_image = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))

        self.pause_icon = pygame.image.load("assets/pauseicon.png").convert_alpha()
        self.pause_icon = pygame.transform.scale(self.pause_icon, (30, 30))

        self.breakable_wall = pygame.image.load("assets/environment/wall.png").convert_alpha()
        self.breakable_wall = pygame.transform.scale(self.breakable_wall, (30, 30))

        self.unbreakable_wall = pygame.image.load("assets/environment/brick.png").convert_alpha()
        self.unbreakable_wall = pygame.transform.scale(self.unbreakable_wall, (30, 30))

        self.blue_cave = pygame.image.load("assets/environment/blue_cave.png").convert_alpha()
        self.blue_cave = pygame.transform.scale(self.blue_cave, (30, 30))
        
        self.red_cave = pygame.image.load("assets/environment/red_cave.png").convert_alpha()
        self.red_cave = pygame.transform.scale(self.red_cave, (30, 30))
        
        self.bomb_icon = pygame.image.load("assets/bomb.png").convert_alpha()
        self.bomb_icon = pygame.transform.scale(self.bomb_icon, (30, 30))

        self.tile_map = copy.deepcopy(selected_map)
        self.available_powerups = ["bomb_powerup", "range_powerup", "freeze_powerup", "live+_powerup", "shield_powerup"]
        self.load_music()
        self.place_hidden_powerups()
        self.trap_image = pygame.image.load("assets/environment/manhole.png").convert_alpha()
        self.trap_image = pygame.transform.scale(self.trap_image, (config.GRID_SIZE, config.GRID_SIZE))
        
    def place_hidden_powerups(self):
        """Place power-ups under random bricks at the start of the game"""
        brick_positions = []

        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                if self.tile_map[y][x] == 2:
                    brick_positions.append((x, y,))

        # Determine how many power-ups to place (e.g., 40% of bricks)
        num_powerups = int(len(brick_positions) * config.POWERUP_SPAWNING_RATE)

        # Randomly select bricks to hide power-ups under
        selected_bricks = random.sample(brick_positions, min(num_powerups, len(brick_positions)))

        # Place power-ups under selected bricks
        for x, y in selected_bricks:
            powerup_type = random.choice(self.available_powerups)
            self.hidden_powerups[(x, y)] = powerup_type  # Only store type here

    def load_music(self):
        self.music_manager.play_music('level', 'level_volume', True)

    def handle_events(self, event):
        # Check if keys are being held or not
        if event.type == pygame.KEYDOWN:
            if event.key in config.PLAYER1_MOVE_KEYS:
                self.player1.held_down_keys.append(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS:
                self.player2.held_down_keys.append(event.key)
            if event.key == pygame.K_p:
                self.game.state_manager.change_state("Pause", self.selected_map, self.map_name)
        elif event.type == pygame.KEYUP:
            if event.key in config.PLAYER1_MOVE_KEYS and event.key in self.player1.held_down_keys:
                self.player1.held_down_keys.remove(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS and event.key in self.player2.held_down_keys:
                self.player2.held_down_keys.remove(event.key)

    def handle_explosions(self):
        # Check if some explosion exists
        if not self.explosion_group:
            return
        if self.player1.check_hit():
            if self.player1.get_health() == 0:
                self.music_manager.play_sound("death", "death_volume")
                pygame.mixer_music.stop()
                self.exit_state()
                self.game.state_manager.change_state("GameOver", self.player2.player_id, self.selected_map, self.map_name)
        elif self.player2.check_hit():
            if self.player2.get_health() == 0:
                self.music_manager.play_sound("death", "death_volume")
                pygame.mixer_music.stop()
                self.exit_state()
                self.game.state_manager.change_state("GameOver", self.player1.player_id, self.selected_map, self.map_name)

    def destroy_tile(self, x, y):
        """Destroy a brick tile and reveal a power-up if one is hidden underneath"""
        # Only handle brick tiles (2)
        if self.tile_map[y][x] == 2:
            # Check if there's a power-up hidden under this brick
            if (x, y) in self.hidden_powerups:
                powerup_type = self.hidden_powerups[(x, y)]
                powerup = PowerUp(x, y, powerup_type)  # You’ll need to update the constructor
                powerup.reveal()
                self.powerup_group.add(powerup)
                del self.hidden_powerups[(x, y)]

            # Update the map (brick is destroyed)
            self.tile_map[y][x] = 0

    def check_powerup_collisions(self):
        """Check if players have collected any power-ups"""
        # Only collect visible (not hidden) power-ups
        visible_powerups = [p for p in self.powerup_group.sprites() if not p.hidden]

        for powerup in visible_powerups:
            # Player 1 collision
            if pygame.sprite.collide_rect(self.player1, powerup):
                self.powerup_message = powerup.apply_effect(self.player1)
                self.message_timer = pygame.time.get_ticks()
                self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                powerup.kill()  # Remove from sprite group
            # Player 2 collision
            if pygame.sprite.collide_rect(self.player2, powerup):
                self.powerup_message = powerup.apply_effect(self.player2)
                self.message_timer = pygame.time.get_ticks()
                self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                powerup.kill()  # Remove from sprite group

    def draw_menu(self, screen):
        player1_lives_text = self.game.font.render(f"x {self.player1.get_health()}", True, config.COLOR_BLACK)
        player2_lives_text = self.game.font.render(f"x {self.player2.get_health()}", True, config.COLOR_BLACK)

        screen.blit(player1_lives_text, (config.GRID_SIZE, 10))
        screen.blit(player2_lives_text, (config.SCREEN_WIDTH - 3 * config.GRID_SIZE, 10))

        screen.blit(self.heart_image, (0, 0))
        screen.blit(self.heart_image, (config.SCREEN_WIDTH - 4 * config.GRID_SIZE, 0))



        player1_bombs = self.game.font.render(f"x {self.player1.get_max_bombs()}", True, config.COLOR_BLACK)
        player2_bombs = self.game.font.render(f"x {self.player2.get_max_bombs()}", True, config.COLOR_BLACK)

        screen.blit(self.bomb_icon, (config.GRID_SIZE * 2, 0))
        screen.blit(self.bomb_icon, (config.SCREEN_WIDTH - 2 * config.GRID_SIZE, 0))

        screen.blit(player1_bombs, (config.GRID_SIZE * 3, 10))
        screen.blit(player2_bombs, (config.SCREEN_WIDTH - config.GRID_SIZE, 10))

        # Display active power-ups for each player
        self.draw_active_powerups(screen)

        # Display power-up message if active
        if self.powerup_message:
            message_text = self.game.font.render(self.powerup_message, True, config.COLOR_BLACK)
            screen.blit(message_text, (config.SCREEN_WIDTH // 2 - message_text.get_width() // 2, 10))
            
    

    def draw_active_powerups(self, screen):
        # Player 1 active power-ups
        p1_powerups_text = []
        p2_powerups_text = []

        for powerup, expire_time in self.player1.active_powerups.items():
            remaining = round(expire_time - time.time(), 2)
            if remaining > 0:
                if powerup == "shield_powerup":
                    p1_powerups_text.append(f"Shield: {remaining}s")
                elif powerup == 'freeze_powerup':
                    p2_powerups_text.append(f'Freeze: {remaining}s')
        for powerup, expire_time in self.player2.active_powerups.items():
            remaining = round(expire_time - time.time(), 2)
            if remaining > 0:
                if powerup == "shield_powerup":
                    p2_powerups_text.append(f"Shield: {remaining}s")
                elif powerup == 'freeze_powerup':
                    p1_powerups_text.append(f'Freeze: {remaining}s')

        # Display Player 1 power-ups
        y_offset = 40
        for text in p1_powerups_text:
            powerup_text = self.game.font.render(text, True, config.COLOR_BLACK)
            screen.blit(powerup_text, (10, y_offset))
            y_offset += 20

        # Display Player 2 power-ups
        y_offset = 40
        for text in p2_powerups_text:
            powerup_text = self.game.font.render(text, True, config.COLOR_BLACK)
            x_pos = config.SCREEN_WIDTH - powerup_text.get_width() - 10
            screen.blit(powerup_text, (x_pos, y_offset))
            y_offset += 20


    def draw_grid(self, screen):
        if self.map_name == "Crystal Caves":
            screen.blit(self.cave_bg, (0, 0))
            pass
        if self.map_name == "Classic":
            screen.blit(self.grass_bg, (0, 0))
            pass
        if self.map_name == "Desert Maze":
            screen.blit(self.sand_bg, (0, 0))
            pass
        if self.map_name == "Ancient Ruins":
            screen.blit(self.ruins_bg, (0, 0))
            pass
        if self.map_name == "Urban Assault":
            screen.blit(self.urban_bg, (0, 0))
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
                        screen.blit(self.unbreakable_stone, (x, y))
                    elif self.map_name in ["Classic", "Desert Maze"]:
                        screen.blit(self.unbreakable_box, (x, y))
                    elif self.map_name == "Ancient Ruins":
                        screen.blit(self.unbreakable_rock, (x, y))
                    else:
                        screen.blit(self.unbreakable_wall, (x, y))
                elif tile == 2:  # Breakable wall
                    if self.map_name == "Desert Maze":
                        screen.blit(self.breakable_cactus, (x, y))
                    elif self.map_name == "Classic":
                        screen.blit(self.breakable_bush, (x, y))
                    elif self.map_name == "Crystal Caves":
                        screen.blit(self.breakable_diamond, (x, y))
                    elif self.map_name == "Ancient Ruins":
                        screen.blit(self.breakable_rock, (x, y))
                    else:
                        screen.blit(self.breakable_wall, (x, y))
                if tile == 4:  # Blue cave
                    screen.blit(self.blue_cave, (x, y))
                if tile == 5:  # Red cave
                    screen.blit(self.red_cave, (x, y))
                elif tile == config.TRAP:  # Poklop
                    screen.blit(self.trap_image, (x, y))

    def draw_players(self, screen):
        screen.blit(self.player1.image, self.player1.rect)
        screen.blit(self.player2.image, self.player2.rect)

        if self.player1.active_powerups.get("shield_powerup"):
            radius = config.GRID_SIZE // 2
            player_center = (self.player1.rect.x + radius, self.player1.rect.y + radius)
            pygame.draw.circle(screen, config.COLOR_LIGHT_BLUE, player_center, radius, width=3)
        elif self.player2.active_powerups.get("shield_powerup"):
            radius = config.GRID_SIZE // 2
            player_center = (self.player2.rect.x + radius, self.player2.rect.y + radius)
            pygame.draw.circle(screen, config.COLOR_LIGHT_BLUE, player_center, radius, width=3)

    def update(self):
        now = pygame.time.get_ticks()

        # Reset moving flags at the start of the frame
        self.player1.moving = False
        self.player2.moving = False

        # Handle player inputs
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

        # ✅ Update animations (idle + walking handled automatically)
        self.player1.update_animation()
        self.player2.update_animation()

        # Check for explosions, power-ups, and other effects
        self.handle_explosions()
        self.check_powerup_collisions()
        self.player1.update_powerups()
        self.player2.update_powerups()

        # Update power-ups group
        self.powerup_group.update()

        self.check_trap_collisions()

        # Clear power-up message after 3 seconds
        if self.message_timer > 0 and now - self.message_timer > 3000:
            self.powerup_message = ""
            self.message_timer = 0

    def check_trap_collisions(self):
        """Skontroluje, či hráči nestúpili na poklop"""
        for player in self.players:
            grid_x = player.rect.x // config.GRID_SIZE
            grid_y = player.rect.y // config.GRID_SIZE

            if (0 <= grid_y < len(self.tile_map)) and \
                    (0 <= grid_x < len(self.tile_map[0])) and \
                    self.tile_map[grid_y][grid_x] == config.TRAP:

                current_time = time.time()
                if not hasattr(player, 'last_trap_time') or current_time - player.last_trap_time > 1.0:
                    player.health = max(0, player.health - 1)
                    player.last_trap_time = current_time

                    # Ak hráč stratil všetky životy
                    if player.health <= 0:
                        self.music_manager.play_sound("death", "death_volume")
                        pygame.mixer_music.stop()
                        self.exit_state()

                        # Zistiť víťaza
                        if player.player_id == 1:
                            winner = self.player2.player_id
                        else:
                            winner = self.player1.player_id

                        self.game.state_manager.change_state("GameOver", winner, self.selected_map, self.map_name)
                    else:
                        self.music_manager.play_sound("death", "death_volume")
                        self.powerup_message = f"Player {player.player_id} fell in a sewer!"
                        self.message_timer = pygame.time.get_ticks()

    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        # Draw playing field
        self.draw_grid(screen)       # ✅ This now draws either background or green grid
        self.draw_walls(screen)
        self.draw_menu(screen)
        self.draw_players(screen)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎮 Draw visible power-ups (not hidden ones)
        self.powerup_group.draw(screen)

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
