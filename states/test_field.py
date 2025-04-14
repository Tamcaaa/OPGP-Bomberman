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
        self.player1 = Player(game, 1)  # Player 1 (WASD)
        self.player2 = Player(game, 2)  # Player 2 (Arrow keys)
        self.game.player1 = self.player1
        self.game.player2 = self.player2
        self.game.all_sprites.add(self.player1)
        self.game.all_sprites.add(self.player2)
        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.heart_image = pygame.image.load("photos/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (32, 32))

    def handle_events(self):
        keys = pygame.key.get_pressed()

        # Player 1 movement controls
        if self.player1 and not self.player1.is_dead:
            self.player1.moving["left"] = keys[pygame.K_a]
            self.player1.moving["right"] = keys[pygame.K_d]
            self.player1.moving["up"] = keys[pygame.K_w]
            self.player1.moving["down"] = keys[pygame.K_s]
            self.player1.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_SPACE])

        # Player 2 movement controls
        if self.player2 and not self.player2.is_dead:
            self.player2.moving["left"] = keys[pygame.K_LEFT]
            self.player2.moving["right"] = keys[pygame.K_RIGHT]
            self.player2.moving["up"] = keys[pygame.K_UP]
            self.player2.moving["down"] = keys[pygame.K_DOWN]
            self.player2.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_RETURN])

    def render(self, screen):
        screen.fill((255, 255, 255))
        self.game.draw_text(screen, "BOMBER-MAN", config.BLACK, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4)

        # Update movement with delta time
        dt = self.game.dt
        if self.player1 and not self.player1.is_dead:
            self.player1.update_movement(dt)
        if self.player2 and not self.player2.is_dead:
            self.player2.update_movement(dt)

        # Update and draw bombs/explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()
        self.player1.update()
        self.player2.update()

        # Check for collisions with explosions (only if players are not dead)
        if self.player1 and not self.player1.is_dead and pygame.sprite.spritecollideany(self.player1,
                                                                                        self.explosion_group):
            self.player1.hit_by_explosion()

        if self.player2 and not self.player2.is_dead and pygame.sprite.spritecollideany(self.player2,
                                                                                        self.explosion_group):
            self.player2.hit_by_explosion()

        # Draw players with blink effect, if not dead
        if self.player1 and not self.player1.is_dead:
            if not self.player1.invincible or self.player1.blink:
                screen.blit(self.player1.image, self.player1.rect)

        if self.player2 and not self.player2.is_dead:
            if not self.player2.invincible or self.player2.blink:
                screen.blit(self.player2.image, self.player2.rect)

        # Draw game objects
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)

        # Draw lives for both players
        if self.player1:
            self.draw_player_lives(screen, self.player1, 10)  # Player 1 lives on left
        if self.player2:
            self.draw_player_lives(screen, self.player2, config.SCREEN_WIDTH - 120)

    def draw_player_lives(self, screen, player, x_pos):
        """Draw lives for a specific player at the given x position."""
        screen.blit(self.heart_image, (x_pos, 10))
        lives_text = self.game.font.render(f"x {player.lives}", True, config.BLACK)
        screen.blit(lives_text, (x_pos + 70, 15))