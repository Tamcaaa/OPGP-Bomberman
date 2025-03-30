import pygame
import config

from states.state import State
from player import Player


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.player = Player()

    def handle_events(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:  # Move left
            self.player.move(-1, 0, "left")
        if keys[pygame.K_d]:  # Move right
            self.player.move(1, 0, "right")
        if keys[pygame.K_w]:  # Move up
            self.player.move(0, -1, "up")
        if keys[pygame.K_s]:  # Move down
            self.player.move(0, 1, "down")

    def render(self, screen):
        screen.fill((255, 255, 255))
        self.game.draw_text(screen, "BOMBER-MAN", config.BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)
        pygame.draw.rect(screen, config.BLACK, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), 1)
        screen.blit(self.player.image, self.player.rect)



