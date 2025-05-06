import copy
import pygame
import config

from states.state import State
from player import Player
from maps.test_field_map import tile_map
from managers.music_manager import MusicManager
from managers.power_up_manager import PowerUpManager


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.game = game
        self.music_manager = MusicManager()
        self.power_up_manager = PowerUpManager()
        self.tile_map = copy.deepcopy(tile_map)

        self.keys_held = {pygame.K_s: False, pygame.K_d: False}

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()

        self.player1 = Player(1, "spawn1", self)
        self.player2 = Player(2, "spawn4", self)

        self.heart_image = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))

        self.breakable_wall = pygame.image.load("assets/environment/wall.png").convert_alpha()
        self.breakable_wall = pygame.transform.scale(self.breakable_wall, (30, 30))

        self.unbreakable_wall = pygame.image.load("assets/environment/brick.png").convert_alpha()
        self.unbreakable_wall = pygame.transform.scale(self.unbreakable_wall, (30, 30))

        self.load_music()

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
        self.tile_map[y][x] = 0
        self.power_up_manager.spawn_power_up(x, y)

    def update(self):
        now = pygame.time.get_ticks()
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

        self.handle_explosions()

    def draw_menu(self, screen):
        player1_lives_text = self.game.font.render(f"x {self.player1.get_health()}", True, config.COLOR_BLACK)
        player2_lives_text = self.game.font.render(f"x {self.player2.get_health()}", True, config.COLOR_BLACK)

        screen.blit(player1_lives_text, (config.GRID_SIZE, 10))
        screen.blit(player2_lives_text, (config.SCREEN_WIDTH - config.GRID_SIZE, 10))

        screen.blit(self.heart_image, (0, 0))
        screen.blit(self.heart_image, (config.SCREEN_WIDTH - 2 * config.GRID_SIZE, 0))

    def draw_power_ups(self, screen):
        for i in self.power_up_manager.get_power_ups():
            print(i)

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

    def render(self, screen):
        screen.fill(config.COLOR_WHITE)

        # Draw playing field
        self.draw_walls(screen)
        self.draw_grid(screen)
        self.draw_menu(screen)
        self.draw_power_ups(screen)

        screen.blit(self.player1.image, self.player1.rect)
        screen.blit(self.player2.image, self.player2.rect)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
