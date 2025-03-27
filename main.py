import pygame
import subprocess

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 400
FONT_SIZE = 24  # Button text font size
H1_SIZE = 54    # H1 title text size
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 30
BUTTON_RADIUS = 4

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BomberMan")

# Load font for the title (H1 size)
h1_font = pygame.font.Font(None, H1_SIZE)
title_text = h1_font.render("BOMBER-MAN", True, BLACK)

# Load font for the button text (button font size)
font = pygame.font.Font(None, FONT_SIZE)

# Load background image
bg_image = pygame.image.load("photos/bg.jpg")
bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))  # Scale image to fit the screen

# Define Button class
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action

    def draw(self, screen):
        # Change button color on hover
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, BUTTON_HOVER_COLOR, self.rect, border_radius=BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=BUTTON_RADIUS)

        # Render the text on the button
        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        # Check if the button is clicked
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False

# Create "Singleplayer" and "Multiplayer" buttons side by side
singleplayer_button = Button(WIDTH // 2 - BUTTON_WIDTH - 20, HEIGHT // 2 - BUTTON_HEIGHT // 2, BUTTON_WIDTH, BUTTON_HEIGHT, "Singleplayer")
multiplayer_button = Button(WIDTH // 2 + 20, HEIGHT // 2 - BUTTON_HEIGHT // 2, BUTTON_WIDTH, BUTTON_HEIGHT, "Multiplayer")

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

    # Fill screen with background image
    screen.blit(bg_image, (0, 0))  # Draw the background image

    # Draw the title text (H1 size)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title_text, title_rect)

    # Draw the buttons
    singleplayer_button.draw(screen)
    multiplayer_button.draw(screen)

    # Check for button clicks
    if singleplayer_button.is_clicked():
        pygame.quit()  # Close menu
        subprocess.run(["python", "Player.py"])  # Run game

    pygame.display.flip()


# Close Pygame properly when exiting the game
pygame.quit()
