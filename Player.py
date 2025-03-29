import sys
import pygame
import os

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
GRID_SIZE = 35
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
MOVE_SPEED = 200

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Creating a screen
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("BomberMan - Singleplayer")


# Load player sprite
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()  # Init
        self.images = {
            "down": pygame.image.load("photos/p_1_down.png").convert_alpha(),
            "up": pygame.image.load("photos/p_1_up.png").convert_alpha(),
            "left": pygame.image.load("photos/p_1_left.png").convert_alpha(),
            "right": pygame.image.load("photos/p_1_right.png").convert_alpha()
        }
        for key in self.images:
            self.images[key] = pygame.transform.scale(self.images[key], (GRID_SIZE, GRID_SIZE))

        self.image = self.images["down"]  # Loading of picture player
        self.image = pygame.transform.scale(self.image, (GRID_SIZE, GRID_SIZE))  # Grid size
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)

        self.move_timer = 0

    def move(self, dx, dy, direction):
        if pygame.time.get_ticks() - self.move_timer > MOVE_SPEED:
            self.rect.x += dx * GRID_SIZE
            self.rect.y += dy * GRID_SIZE

            # Boundary correction
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - GRID_SIZE))
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - GRID_SIZE))

            # Update sprite based on direction
            self.image = self.images[direction]

            self.move_timer = pygame.time.get_ticks()


# Creation of player
player = Player()

# FPS regulation
clock = pygame.time.Clock()

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    # Key handling
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:  # Move left
        player.move(-1, 0, "left")
    if keys[pygame.K_d]:  # Move right
        player.move(1, 0, "right")
    if keys[pygame.K_w]:  # Move up
        player.move(0, -1, "up")
    if keys[pygame.K_s]:  # Move down
        player.move(0, 1, "down")

    # Render player
    pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 1)
    screen.blit(player.image, player.rect)

    pygame.display.flip()
    clock.tick(120)  # FPS limit

pygame.quit()

sys.exit()
