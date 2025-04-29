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

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()

        self.player1 = Player(1, "spawn1", self.bomb_group, self.explosion_group)
        self.player2 = Player(2, "spawn4", self.bomb_group, self.explosion_group)

    def handle_events(self, event):

        if not event.type == pygame.KEYDOWN:
            return
        if event.key in config.PLAYER1_MOVE_KEYS:
            if len(self.player1.queued_keys) < config.MAX_QUEUE:
                self.player1.queued_keys.append(event.key)
        elif event.key in config.PLAYER2_MOVE_KEYS:
            if len(self.player2.queued_keys) < config.MAX_QUEUE:
                self.player2.queued_keys.append(event.key)

    def update(self):
        now = pygame.time.get_ticks()
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)

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

        screen.blit(self.player1.image, self.player1.rect)
        screen.blit(self.player2.image, self.player2.rect)

        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
