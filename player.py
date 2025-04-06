import pygame
import config
import time
from bomb import Bomb
from config import *
from states.game_over import GameOver  # Import the GameOver class

class Player(pygame.sprite.Sprite):
    def __init__(self,game):
        super().__init__()
        self.game = game
        global currentBomb  # Global variable access
        self.lives = PLAYER_LIVES
        self.last_hit_time = 0
        self.hit_cooldown = 1.0
        self.currentBomb = 1  # Store in instance
        self.maxBombs = 1
        self.power = 1

        # Load and scale images for each direction
        self.images = {
            "down": pygame.image.load("photos/player_color/p_1_down.png").convert_alpha(),
            "up": pygame.image.load("photos/player_color/p_1_up.png").convert_alpha(),
            "left": pygame.image.load("photos/player_color/p_1_left.png").convert_alpha(),
            "right": pygame.image.load("photos/player_color/p_1_right.png").convert_alpha()
        }

        for key in self.images:
            self.images[key] = pygame.transform.scale(self.images[key], (config.GRID_SIZE, config.GRID_SIZE))

        self.image = self.images["down"]  # Default direction image
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)  # Initial position
        self.move_timer = 0  # Timer for movement delay
        self.rect.topleft = (0,0)

    def move(self, dx, dy, direction):
        """Move the player and update sprite based on direction."""
        if pygame.time.get_ticks() - self.move_timer > config.MOVE_SPEED:
            self.rect.x += dx * config.GRID_SIZE
            self.rect.y += dy * config.GRID_SIZE

            # Boundary correction
            self.rect.x = max(0, min(self.rect.x, config.SCREEN_WIDTH - config.GRID_SIZE))
            self.rect.y = max(0, min(self.rect.y, config.SCREEN_HEIGHT - config.GRID_SIZE))

            self.image = self.images[direction]  # Update sprite direction
            self.move_timer = pygame.time.get_ticks()  # Reset move timer
            
    def deployBomb(self, bomb_group, explosion_group):
        if self.currentBomb > 0:
            Bomb(self, bomb_group, explosion_group)  # Use the correct Bomb class
            self.currentBomb -= 1  # Create bomb instance  
          
    def enter_game_over(self):
        """Switch to the Game Over state when the player loses all lives."""
        from states.game_over import GameOver  # Import here to avoid circular import
        new_state = GameOver(self.game)
        new_state.enter_state()
        
    def loseLife(self):
        self.lives -= 1
        if self.lives == 0:
            self.enter_game_over()  # Game Over when no lives are left
    
    def take_lives(self):
        current_time = time.time()
        if current_time - self.last_hit_time >= self.hit_cooldown:
            self.loseLife()
            self.last_hit_time = current_time
