import pygame
import config


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Load and scale images for each direction
        self.images = {
            "down": pygame.image.load("photos/p_1_down.png").convert_alpha(),
            "up": pygame.image.load("photos/p_1_up.png").convert_alpha(),
            "left": pygame.image.load("photos/p_1_left.png").convert_alpha(),
            "right": pygame.image.load("photos/p_1_right.png").convert_alpha()
        }
        for key in self.images:
            self.images[key] = pygame.transform.scale(self.images[key], (config.GRID_SIZE, config.GRID_SIZE))

        self.image = self.images["down"]  # Default direction image
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)  # Initial position
        self.move_timer = 0  # Timer for movement delay

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