import pygame
import config

from states.state import State
from player import Player
from level import Level  # Import the Level class we created


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
        
        # Initialize the level
        self.level = Level()
        # Try to load a level from file, or generate a standard one if loading fails
        if not self.level.load_level("levels/level1.txt"):
            self.level.generate_standard_level()
        
        # Initialize players at appropriate starting positions
        # Player 1 starts at top-left corner (with a bit of offset)
        self.player1 = Player(game, 1)
        self.player1.rect.x = config.GRID_SIZE
        self.player1.rect.y = config.GRID_SIZE
        
        # Player 2 starts at bottom-right corner (with a bit of offset)
        self.player2 = Player(game, 2)
        self.player2.rect.x = (self.level.width - 2) * config.GRID_SIZE
        self.player2.rect.y = (self.level.height - 2) * config.GRID_SIZE
        
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
                self.check_collision(self.player1)
            if keys[pygame.K_d]:  # Move right
                self.player1.move(1, 0, "right")
                self.check_collision(self.player1)
            if keys[pygame.K_w]:  # Move up
                self.player1.move(0, -1, "up")
                self.check_collision(self.player1)
            if keys[pygame.K_s]:  # Move down
                self.player1.move(0, 1, "down")
                self.check_collision(self.player1)
            self.player1.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_SPACE])

        # Player 2 controls (Arrow keys + ENTER/RETURN)
        if self.player2 and not self.player2.is_dead:
            if keys[pygame.K_LEFT]:
                self.player2.move(-1, 0, "left")
                self.check_collision(self.player2)
            if keys[pygame.K_RIGHT]:
                self.player2.move(1, 0, "right")
                self.check_collision(self.player2)
            if keys[pygame.K_UP]:
                self.player2.move(0, -1, "up")
                self.check_collision(self.player2)
            if keys[pygame.K_DOWN]:
                self.player2.move(0, 1, "down")
                self.check_collision(self.player2)
            self.player2.handle_bomb_placement(self.bomb_group, self.explosion_group, keys[pygame.K_RETURN])

    def check_collision(self, player):
        """Check if player is colliding with walls or bricks and adjust position"""
        # Get the grid coordinates
        grid_x = player.rect.centerx // config.GRID_SIZE
        grid_y = player.rect.centery // config.GRID_SIZE
        
        # Check the surrounding tiles
        for y_offset in [-1, 0, 1]:
            for x_offset in [-1, 0, 1]:
                check_x = grid_x + x_offset
                check_y = grid_y + y_offset
                
                # Skip if out of bounds
                if check_x < 0 or check_x >= self.level.width or check_y < 0 or check_y >= self.level.height:
                    continue
                
                # If the tile is a wall or brick, check for collision
                if self.level.grid[check_y][check_x] != 0:  # Not empty
                    # Create a rect for this tile
                    tile_rect = pygame.Rect(
                        check_x * config.GRID_SIZE,
                        check_y * config.GRID_SIZE,
                        config.GRID_SIZE,
                        config.GRID_SIZE
                    )
                    
                    # If colliding, adjust position
                    if player.rect.colliderect(tile_rect):
                        # Calculate overlap
                        dx = player.rect.centerx - tile_rect.centerx
                        dy = player.rect.centery - tile_rect.centery
                        
                        # Push player in direction of least overlap
                        if abs(dx) > abs(dy):
                            if dx > 0:
                                player.rect.left = tile_rect.right
                            else:
                                player.rect.right = tile_rect.left
                        else:
                            if dy > 0:
                                player.rect.top = tile_rect.bottom
                            else:
                                player.rect.bottom = tile_rect.top

    def render(self, screen):
        screen.fill((255, 255, 255))
        
        # Draw the level first (as background)
        self.level.draw(screen)

        # Update and draw bombs/explosions
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()
        
        # Update players
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
        
    def place_bomb_on_level(self, x, y):
        """Convert player position to grid position for bomb placement"""
        grid_x = x // config.GRID_SIZE
        grid_y = y // config.GRID_SIZE
        return grid_x, grid_y