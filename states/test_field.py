import copy
import pygame
import config
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

        self.keys_held = {pygame.K_s: False, pygame.K_d: False}

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

        self.breakable_wall = pygame.image.load("assets/environment/wall.png").convert_alpha()
        self.breakable_wall = pygame.transform.scale(self.breakable_wall, (30, 30))

        self.unbreakable_wall = pygame.image.load("assets/environment/brick.png").convert_alpha()
        self.unbreakable_wall = pygame.transform.scale(self.unbreakable_wall, (30, 30))

        self.bomb_icon = pygame.image.load("assets/bomb.png").convert_alpha()
        self.bomb_icon = pygame.transform.scale(self.bomb_icon, (30, 30))

        self.load_music()

        # Place power-ups under random bricks at the start
        self.place_hidden_powerups()

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
            # Create a hidden power-up (not added to sprite group yet)
            powerup = PowerUp(x, y, 'range_powerup')
            self.hidden_powerups[(x, y)] = powerup

    def load_music(self):
        self.music_manager.play_music('level', 'level_volume', True)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in config.PLAYER1_MOVE_KEYS:
                self.player1.held_down_keys.append(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS:
                self.player2.held_down_keys.append(event.key)
        elif event.type == pygame.KEYUP:
            if event.key in config.PLAYER1_MOVE_KEYS:
                self.player1.held_down_keys.remove(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS:
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
        """Display active power-ups for each player"""
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
                if tile == 0:
                    rect = pygame.Rect(col_index * config.GRID_SIZE, row_index * config.GRID_SIZE, config.GRID_SIZE,
                                       config.GRID_SIZE)
                    pygame.draw.rect(screen, config.COLOR_DARK_GREEN if (col_index + row_index) % 2 == 0 else config.COLOR_LIGHT_GREEN,
                                     rect)
                elif tile == 1:
                    screen.blit(self.unbreakable_wall, (col_index * config.GRID_SIZE, row_index * config.GRID_SIZE))
                elif tile == 2:
                    screen.blit(self.breakable_wall, (col_index * config.GRID_SIZE, row_index * config.GRID_SIZE))

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
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

        self.handle_explosions()
        self.check_powerup_collisions()

        self.player1.update_powerups()
        self.player2.update_powerups()

        # Update power-ups
        self.powerup_group.update()

        # Clear message after 3 seconds
        if self.message_timer > 0 and now - self.message_timer > 3000:
            self.powerup_message = ""
            self.message_timer = 0

    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        # Draw playing field
        self.draw_walls(screen)
        self.draw_grid(screen)
        self.draw_menu(screen)

        # Draw Players
        self.draw_players(screen)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎮 Draw visible power-ups (not hidden ones)
        self.powerup_group.draw(screen)

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
