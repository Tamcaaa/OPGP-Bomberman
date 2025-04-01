import pygame
import config
import time

class Bomb(pygame.sprite.Sprite):
    def __init__(self, player, bomb_group):
        super().__init__()
        
        # Load and scale the bomb image
        self.image = pygame.image.load("photos/bomb.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (config.GRID_SIZE, config.GRID_SIZE))
        
        # Set bomb position to player's current position
        self.rect = self.image.get_rect()
        self.rect.topleft = player.rect.topleft
        
        # Bomb properties
        self.range = player.power  # Explosion range
        self.player = player
        self.fuse_time = time.time() + 3  # Bomb explodes after 3 seconds
        
        # Add the bomb to the bomb group
        bomb_group.add(self)
    
    def update(self):
        """Update method to check if the bomb should explode."""
        if time.time() >= self.fuse_time:
            self.explode()
    
    def explode(self):
        """Handles the bomb explosion and removes it from the game."""
        print("Bomb exploded!")  # Placeholder for explosion animation
        self.player.currentBomb += 1  # Allow the player to place another bomb
        self.kill()  # Remove the bomb from the group