import copy
import pygame
import config
import os

from states.state import State
from player import Player
from maps.test_field_map import tile_map
from managers.music_manager import MusicManager


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.game = game

        self.music_manager = MusicManager()
        self.tile_map = copy.deepcopy(tile_map)

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()

        self.player1 = Player(1, "spawn1", self)
        self.player2 = Player(2, "spawn4", self)

        self.heart_image = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))

        self.load_music()

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
        self.tile_map[y][x] = 0

    def update(self):
        now = pygame.time.get_ticks()
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

        self.handle_explosions()

    def draw_menu(self, screen):
        screen.blit(self.player1.image, self.player1.rect)
        screen.blit(self.player2.image, self.player2.rect)

        player1_lives_text = self.game.font.render(f"x {self.player1.get_health()}", True, config.COLOR_BLACK)
        player2_lives_text = self.game.font.render(f"x {self.player2.get_health()}", True, config.COLOR_BLACK)

        screen.blit(player1_lives_text, (config.GRID_SIZE, 10))
        screen.blit(player2_lives_text, (config.SCREEN_WIDTH - config.GRID_SIZE, 10))

        screen.blit(self.heart_image, (0, 0))
        screen.blit(self.heart_image, (config.SCREEN_WIDTH - 2 * config.GRID_SIZE, 0))

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
                if tile == 1:
                    rect = pygame.Rect(col_index * config.GRID_SIZE, row_index * config.GRID_SIZE, config.GRID_SIZE,
                                       config.GRID_SIZE)
                    pygame.draw.rect(screen, config.COLOR_BLACK, rect)
                elif tile == 2:
                    rect = pygame.Rect(col_index * config.GRID_SIZE, row_index * config.GRID_SIZE, config.GRID_SIZE,
                                       config.GRID_SIZE)
                    pygame.draw.rect(screen, config.COLOR_GREEN, rect)

    def render(self, screen):
        screen.fill((255, 255, 255))

        # Draw playing field
        self.draw_grid(screen)
        self.draw_walls(screen)
        self.draw_menu(screen)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
