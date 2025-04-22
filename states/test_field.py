import pygame

import config

from states.state import State
from player import Player
from bomb import Bomb
from bomb import Explosion
from maps.test_field_map import tile_map


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.game = game
        self.player = Player()
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.last_move_time = 0
        self.move_cooldown = config.MOVE_COOLDOWN
        self.queued_keys = []
        self.MOVE_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]
        self.MAX_QUEUE = 3


        # Draw environment only once
    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.MOVE_KEYS:
                if len(self.queued_keys) < self.MAX_QUEUE:
                    self.queued_keys.append(event.key)
            elif event.key == pygame.K_SPACE:
                self.queued_keys.append(event.key)

    def update(self):
        now = pygame.time.get_ticks()
        if self.queued_keys and now - self.last_move_time >= config.MOVE_COOLDOWN:
            key = self.queued_keys.pop(0)
            if key == pygame.K_w:
                self.player.move(0, -1, "up")
            elif key == pygame.K_s:
                self.player.move(0, 1, "down")
            elif key == pygame.K_a:
                self.player.move(-1, 0, "left")
            elif key == pygame.K_d:
                self.player.move(1, 0, "right")
            elif key == pygame.K_SPACE:
                self.player.deploy_bomb(self.bomb_group, self.explosion_group)
            self.last_move_time = now

    def render(self, screen):
        screen.fill((255, 255, 255))

        for line in range((config.SCREEN_WIDTH // config.GRID_SIZE) + 1):
            pygame.draw.line(screen, config.BLACK, (line * config.GRID_SIZE, 0),
                             (line * config.GRID_SIZE, config.SCREEN_HEIGHT))
        for line in range((config.SCREEN_HEIGHT // config.GRID_SIZE) + 1):
            pygame.draw.line(screen, config.BLACK, (0, line * config.GRID_SIZE),
                             (config.SCREEN_WIDTH, line * config.GRID_SIZE))

        for row_index, row in enumerate(tile_map):
            for col_index, tile in enumerate(row):
                if tile == 1:
                    rect = pygame.Rect(col_index * config.GRID_SIZE, row_index * config.GRID_SIZE, config.GRID_SIZE,
                                       config.GRID_SIZE)
                    pygame.draw.rect(screen, config.BLACK, rect)


        pygame.draw.rect(screen, config.BLACK, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), 1)
        screen.blit(self.player.image, self.player.rect)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
