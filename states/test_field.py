import pygame
import config

from states.state import State
from player import Player


class TestField(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: TestField")
        
        # Initialize pygame mixer for background music
        pygame.mixer.init()
        
        # Load and play background music
        pygame.mixer.music.load("sounds/Boss Battle (BDS).mp3")
        pygame.mixer.music.set_volume(0.5)  # Set volume to 50%, adjust as needed
        pygame.mixer.music.play(-1, 0.0)  # Loop music indefinitely
        
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

        if self.player1 and not self.player1.is_dead:
            if keys[pygame.K_a]:  # Move left
                self.player1.move(-1, 0, "left")
            if keys[pygame.K_d]:  # Move right
                self.player1.move(1, 0, "right")
            if keys[pygame.K_w]:  # Move up
                self.player1.move(0, -1, "up")
            if keys[pygame.K_s]:  # Move down
                self.player1.move(0, 1, "down")
            self.player1.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_SPACE])

        # Player 2 controls (Arrow keys + ENTER/RETURN)
        if self.player2 and not self.player2.is_dead:
            if keys[pygame.K_LEFT]:
                self.player2.move(-1, 0, "left")
            if keys[pygame.K_RIGHT]:
                self.player2.move(1, 0, "right")
            if keys[pygame.K_UP]:
                self.player2.move(0, -1, "up")
            if keys[pygame.K_DOWN]:
                self.player2.move(0, 1, "down")
            self.player2.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_RETURN])

    def render(self, screen):
        screen.fill((255, 255, 255))

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

        # Check if both players are dead and stop music
        if self.player1.is_dead and self.player2.is_dead:
            pygame.mixer.music.stop()  # Stop the current background music
            self.play_game_over_music()  # Play "Game Over" music
            self.show_game_over(screen)  # Show game over screen

    def play_game_over_music(self):
        """Play the 'Game Over' music when both players die."""
        pygame.mixer.music.load("sounds/19 Game Over.mp3")  # Load the "Game Over" music
        pygame.mixer.music.set_volume(0.5)  # Set volume to 50%, adjust as needed
        pygame.mixer.music.play(0, 0.0)  # Play the "Game Over" music once

    def show_game_over(self, screen):
        """Display the game over screen when both players die."""
        game_over_text = self.game.font.render("GAME OVER", True, config.BLACK)
        screen.blit(game_over_text, (config.SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                                    config.SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
        pygame.display.update()

    def draw_player_lives(self, screen, player, x_pos):
        """Draw lives for a specific player at the given x position."""
        screen.blit(self.heart_image, (x_pos, 10))
        lives_text = self.game.font.render(f"x {player.lives}", True, config.BLACK)
        screen.blit(lives_text, (x_pos + 70, 15))
