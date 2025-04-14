import pygame
import config

from states.state import State
from player import Player
from bomb import Bomb
from bomb import Explosion


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        self.player = Player()
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        
    def handle_events(self,event):
        if pygame.time.get_ticks() - self.player.move_timer >= self.player.move_cooldown:
            if pygame.KEYDOWN == event.type:
                if event.key == pygame.K_a:  # Move left
                    self.player.move(-1, 0, "left")
                elif event.key == pygame.K_d:  # Move right
                    self.player.move(1, 0, "right")
                elif event.key == pygame.K_w:  # Move up
                    self.player.move(0, -1, "up")
                elif event.key == pygame.K_s:  # Move down
                    self.player.move(0, 1, "down")
                if event.key == pygame.K_SPACE: # Place a bomb
                    self.player.deploy_bomb(self.bomb_group, self.explosion_group)


    def render(self, screen):
        screen.fill((255, 255, 255))
        self.game.draw_text(screen, "BOMBER-MAN", config.BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)
        pygame.draw.rect(screen, config.BLACK, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), 1)
        screen.blit(self.player.image, self.player.rect)
        
        # 🔥 Update explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()

        # 🎨 Draw objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)
        

