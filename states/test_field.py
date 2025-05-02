import copy
import pygame
import config
import os
import time
import random

from states.state import State
from player import Player
from maps.test_field_map import tile_map
from managers.music_manager import MusicManager
from power_up import PowerUp


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.game = game

        self.music_manager = MusicManager()
        self.tile_map = copy.deepcopy(tile_map)
        
        # Remove door and key from the map (replace with empty tiles)
        self.remove_door_and_key()

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()  # Group for power-ups
        
        # Hidden power-ups map - stores which bricks have power-ups underneath
        self.hidden_powerups = {}  # Format: {(x, y): powerup_type}

        self.player1 = Player(1, "spawn1", self)
        self.player2 = Player(2, "spawn4", self)
        self.players = [self.player1, self.player2]
        
        # Feedback message for power-ups
        self.powerup_message = ""
        self.message_timer = 0
        
        # Load images
        self.heart_image = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))
        
        self.wall_image = pygame.image.load("assets/wall.png").convert_alpha()
        self.wall_image = pygame.transform.scale(self.wall_image, (30, 30))

        self.brick_image = pygame.image.load("assets/brick.png").convert_alpha()
        self.brick_image = pygame.transform.scale(self.brick_image, (30, 30))
        
        self.ground_image = pygame.image.load("assets/floor.png").convert_alpha()
        self.ground_image = pygame.transform.scale(self.ground_image, (30, 30))

        self.load_music()
        
        # Place power-ups under random bricks at the start
        self.place_hidden_powerups()

    def remove_door_and_key(self):
        """Remove door and key tiles from the map"""
        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                # Replace door and key tiles (4, 5, 6, 7) with empty tiles (0)
                if self.tile_map[y][x] in [4, 5, 6, 7]:
                    self.tile_map[y][x] = 0

    def place_hidden_powerups(self):
        """Place power-ups under random bricks at the start of the game"""
        brick_positions = []
        
        # Find all brick tiles
        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                if self.tile_map[y][x] == 2:  # Brick
                    brick_positions.append((x, y))
        
        # Determine how many power-ups to place (e.g., 40% of bricks)
        num_powerups = int(len(brick_positions) * config.POWERUP_SPAWNING_RATE)
        
        # Randomly select bricks to hide power-ups under
        selected_bricks = random.sample(brick_positions, min(num_powerups, len(brick_positions)))
        
        # Place power-ups under selected bricks
        for x, y in selected_bricks:
            # Create a hidden power-up (not added to sprite group yet)
            powerup = PowerUp(x, y)
            self.hidden_powerups[(x, y)] = powerup

    def load_music(self):
        self.music_manager.play_music('level', 'level_volume', True)

    def handle_events(self, event):
        if not event.type == pygame.KEYDOWN:
            return
        if event.key in config.PLAYER1_MOVE_KEYS:
            if len(self.player1.queued_keys) < config.MAX_QUEUE:
                self.player1.queued_keys.append(event.key)
        elif event.key in config.PLAYER2_MOVE_KEYS:
            if len(self.player2.queued_keys) < config.MAX_QUEUE:
                self.player2.queued_keys.append(event.key)

    def handle_explosions(self):
        # Check if some explosion exists
        if not self.explosion_group:
            return
            
        # Check for brick destruction by explosions
        for explosion in self.explosion_group:
            explosion_x = explosion.rect.x // config.GRID_SIZE
            explosion_y = explosion.rect.y // config.GRID_SIZE
            
            # If explosion is on a brick, destroy it
            if 0 <= explosion_y < len(self.tile_map) and 0 <= explosion_x < len(self.tile_map[0]):
                if self.tile_map[explosion_y][explosion_x] == 2:  # If it's a brick
                    self.destroy_tile(explosion_x, explosion_y)
        
        # Check player hits
        if self.player1.check_hit():
            if self.player1.get_health() == 0:
                self.music_manager.play_sound("death","death_volume")
                pygame.mixer_music.stop()
                self.exit_state()
                self.game.state_manager.change_state("GameOver", self.player2.player_id)
        elif self.player2.check_hit():
            if self.player2.get_health() == 0:
                self.music_manager.play_sound("death", "death_volume")
                pygame.mixer_music.stop()
                self.exit_state()
                self.game.state_manager.change_state("GameOver", self.player1.player_id)

    def destroy_tile(self, x, y):
        """Destroy a brick tile and reveal a power-up if one is hidden underneath"""
        # Only handle brick tiles (2)
        if self.tile_map[y][x] == 2:
            # Check if there's a power-up hidden under this brick
            if (x, y) in self.hidden_powerups:
                # Reveal the hidden power-up
                powerup = self.hidden_powerups[(x, y)]
                powerup.reveal()  # Mark as revealed
                self.powerup_group.add(powerup)  # Add to visible sprites
                del self.hidden_powerups[(x, y)]  # Remove from hidden collection
                
            # Update the map (brick is destroyed)
            self.tile_map[y][x] = 0

    def check_powerup_collisions(self):
        """Check if players have collected any power-ups"""
        # Only collect visible (not hidden) power-ups
        visible_powerups = [p for p in self.powerup_group.sprites() if not p.hidden]
        
        # Player 1 collisions
        for powerup in visible_powerups:
            if pygame.sprite.collide_rect(self.player1, powerup):
                self.powerup_message = powerup.apply_effect(self.player1)
                self.message_timer = pygame.time.get_ticks()
                self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                powerup.kill()  # Remove from sprite group
            
        # Player 2 collisions
        for powerup in visible_powerups:
            if pygame.sprite.collide_rect(self.player2, powerup):
                self.powerup_message = powerup.apply_effect(self.player2)
                self.message_timer = pygame.time.get_ticks()
                self.music_manager.play_sound("walk", "walk_volume")  # Play pickup sound
                powerup.kill()  # Remove from sprite group

    def update(self):
        now = pygame.time.get_ticks()
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

        self.handle_explosions()
        self.check_powerup_collisions()
        
        # Update power-ups
        self.powerup_group.update()
        
        # Clear message after 3 seconds
        if self.message_timer > 0 and now - self.message_timer > 3000:
            self.powerup_message = ""
            self.message_timer = 0
            
    

    def draw_menu(self, screen):
        screen.blit(self.player1.image, self.player1.rect)
        screen.blit(self.player2.image, self.player2.rect)

        # Display player health
        player1_lives_text = self.game.font.render(f"x {self.player1.get_health()}", True, config.COLOR_BLACK)
        player2_lives_text = self.game.font.render(f"x {self.player2.get_health()}", True, config.COLOR_BLACK)

        screen.blit(player1_lives_text, (config.GRID_SIZE, 10))
        screen.blit(player2_lives_text, (config.SCREEN_WIDTH - config.GRID_SIZE, 10))

        screen.blit(self.heart_image, (0, 0))
        screen.blit(self.heart_image, (config.SCREEN_WIDTH - 2 * config.GRID_SIZE, 0))
        
        # Display active power-ups for each player
        self.draw_active_powerups(screen)
        
        # Display power-up message if active
        if self.powerup_message:
            message_text = self.game.font.render(self.powerup_message, True, config.COLOR_BLACK)
            screen.blit(message_text, (config.SCREEN_WIDTH // 2 - message_text.get_width() // 2, 10))

    def draw_active_powerups(self, screen):
        """Display active power-ups for each player"""
        # Player 1 active power-ups
        p1_powerups_text = []
        for powerup, expire_time in self.player1.active_powerups.items():
            remaining = int(expire_time - time.time())
            if remaining > 0:
                if powerup == "bomb_powerup":
                    p1_powerups_text.append(f"Bombs+: {remaining}s")
                elif powerup == "speed_powerup":
                    p1_powerups_text.append(f"Range+: {remaining}s")
                elif powerup == "shield_powerup":
                    p1_powerups_text.append(f"Shield: {remaining}s")
                    
        # Player 2 active power-ups
        p2_powerups_text = []
        for powerup, expire_time in self.player2.active_powerups.items():
            remaining = int(expire_time - time.time())
            if remaining > 0:
                if powerup == "bomb_powerup":
                    p2_powerups_text.append(f"Bombs+: {remaining}s")
                elif powerup == "speed_powerup":
                    p2_powerups_text.append(f"Range+: {remaining}s")
                elif powerup == "shield_powerup":
                    p2_powerups_text.append(f"Shield: {remaining}s")
        
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

    @staticmethod
    def draw_grid(screen):
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

                if tile == 1:
                    screen.blit(self.wall_image, (x, y))
                elif tile == 2:
                    screen.blit(self.brick_image, (x, y))

    def render(self, screen):
        screen.fill(config.BACKGROUND_COLOR)

        # Draw playing field
        self.draw_grid(screen)
        self.draw_walls(screen)
        self.draw_menu(screen)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎮 Draw visible power-ups (not hidden ones)
        self.powerup_group.draw(screen)
        
        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)