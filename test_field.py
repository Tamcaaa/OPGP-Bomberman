import pygame
from state import State


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")

    def render(self, screen):
        screen.fill((255, 255, 255))
        self.game.draw_text(screen, "BOMBER-MAN", (0, 0, 0), self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT // 4)
