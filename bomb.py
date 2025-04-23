import pygame
import config
import time
from config import FUSE_TIME
pygame.init()
pygame.mixer.init()

explosion_sound = pygame.mixer.Sound("sounds/explosion.mp3")

class Bomb(pygame.sprite.Sprite):
    def __init__(self, player, bomb_group, explosion_group):
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
        self.fuse_time = time.time() + FUSE_TIME  # Bomb explodes after 3 seconds
        self.explosion_group = explosion_group
        # Add the bomb to the bomb group
        bomb_group.add(self)

    def update(self, explosion_group):
        """Update method to check if the bomb should explode."""
        if time.time() >= self.fuse_time:
            self.explode(explosion_group)

    def explode(self, explosion_group):
        """Handles the bomb explosion and removes it from the game."""
        print("Bomb exploded!") # Placeholder for explosion animation
        explosion_sound.play()
        Explosion(self.rect.x, self.rect.y, explosion_group, self.range)
        self.player.currentBomb -= 1  # Allow the player to place another bomb
        self.kill()  # Remove the bomb from the group


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, explosion_group, explosion_range):
        super().__init__()

        # Load explosion image
        self.image_a = pygame.image.load("photos/explosion_a.png").convert_alpha()
        self.image_c = pygame.image.load("photos/explosion_c.png").convert_alpha()

        # Scale images
        self.image_a = pygame.transform.scale(self.image_a, (config.GRID_SIZE, config.GRID_SIZE))
        self.image_c = pygame.transform.scale(self.image_c, (config.GRID_SIZE, config.GRID_SIZE))

        # Set initial image
        self.image = self.image_a  # Corrected: Assign self.image properly
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        # Timing for switching images
        self.start_time = time.time()
        self.switch_time = self.start_time + config.SWITCH_TIME_EXPLOSION # Switch to explosion_c after 0.25s
        self.lifetime = config.BOMB_LIFETIME # Remove after 0.5s

        explosion_group.add(self)  # Add explosion to group

        self.create_explosions(x, y, explosion_group, explosion_range)

    def create_explosions(self, x, y, explosion_group, explosion_range):
        """Generate explosion sprites in all four directions."""
        directions = [(0, 0), (0, 0), (0, 0), (0, 0)]  # Right, Left, Down, Up
        for dx, dy in directions:
            for i in range(1, explosion_range + 1):
                new_x = x + dx * config.GRID_SIZE * i
                new_y = y + dy * config.GRID_SIZE * i
                explosion = Explosion(new_x, new_y, explosion_group, 0)  # Create explosion effect
                explosion_group.add(explosion)

    def update(self):
        """Remove explosion after lifetime expires."""
        current_time = time.time()
        # Switch to explosion_c after 0.25s
        if current_time >= self.switch_time and self.image != self.image_c:
            self.image = self.image_c

        # Remove explosion after lifetime expires
        if current_time - self.start_time > self.lifetime:
            self.kill()
