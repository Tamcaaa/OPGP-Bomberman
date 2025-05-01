import pygame
import config
import time
from managers.music_manager import MusicManager


class Bomb(pygame.sprite.Sprite):
    def __init__(self, player, bomb_group, explosion_group, test_field):
        super().__init__()

        self.test_field = test_field
        self.music_manager = MusicManager()

        # Load and scale the bomb image
        self.image = pygame.image.load("assets/bomb.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (config.GRID_SIZE, config.GRID_SIZE))

        # Set bomb position to player's current position
        self.rect = self.image.get_rect()
        self.rect.topleft = player.rect.topleft

        # Bomb properties
        self.range = player.power  # Explosion range
        self.player = player
        self.fuse_time = time.time() + 3  # Bomb explodes after 3 seconds
        self.explosion_group = explosion_group
        # Add the bomb to the bomb group
        bomb_group.add(self)

    def update(self, explosion_group):
        """Update method to check if the bomb should explode."""
        if time.time() >= self.fuse_time:
            self.explode(explosion_group)

    def explode(self, explosion_group):
        """Handles the bomb explosion and removes it from the game."""
        self.music_manager.play_sound("explosion", "explosion_volume")
        Explosion(self.rect.x, self.rect.y, explosion_group, self.range, self.test_field)
        self.player.currentBomb += 1  # Allow the player to place another bomb
        self.kill()  # Remove the bomb from the group


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, explosion_group, explosion_range, test_field):
        super().__init__()

        self.test_field = test_field
        # Load explosion image
        self.image_a = pygame.image.load("assets/explosion_a.png").convert_alpha()
        self.image_c = pygame.image.load("assets/explosion_c.png").convert_alpha()

        # Scale images
        self.image_a = pygame.transform.scale(self.image_a, (config.GRID_SIZE, config.GRID_SIZE))
        self.image_c = pygame.transform.scale(self.image_c, (config.GRID_SIZE, config.GRID_SIZE))

        # Set initial image
        self.image = self.image_a  # Corrected: Assign self.image properly
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        # Timing for switching images
        self.start_time = time.time()
        self.switch_time = self.start_time + 0.25  # Switch to explosion_c after 0.25s
        self.lifetime = 0.5  # Remove after 0.5s

        explosion_group.add(self)  # Add explosion to group

        self.create_explosions(x, y, explosion_group, explosion_range)

    def create_explosions(self, x, y, explosion_group, explosion_range):
        """Generate explosion sprites in all four directions."""
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Right, Left, Down, Up
        for dx, dy in directions:
            for i in range(1, explosion_range + 1):
                tile_x = (x + dx * config.GRID_SIZE * i) // config.GRID_SIZE
                tile_y = (y + dy * config.GRID_SIZE * i) // config.GRID_SIZE

                max_x = (config.SCREEN_WIDTH - config.GRID_SIZE) // config.GRID_SIZE
                max_y = (config.SCREEN_HEIGHT - config.GRID_SIZE) // config.GRID_SIZE

                new_x = tile_x * config.GRID_SIZE
                new_y = tile_y * config.GRID_SIZE
                if not (0 <= tile_x <= max_x and 0 <= tile_y <= max_y):
                    continue
                elif self.test_field.tile_map[tile_y][tile_x] == 0:
                    explosion = Explosion(new_x, new_y, explosion_group, 0, self.test_field)  # Create explosion effect
                    explosion_group.add(explosion)
                elif self.test_field.tile_map[tile_y][tile_x] == 2:
                    self.test_field.destroy_tile(tile_x, tile_y)
                    explosion = Explosion(new_x, new_y, explosion_group, 0, self.test_field)  # Create explosion effect
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
