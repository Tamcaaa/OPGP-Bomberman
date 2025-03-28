import pygame
import subprocess

# Constants
WIDTH, HEIGHT = 800, 400
FONT_SIZE = 24  # Button text font size
H1_SIZE = 54  # H1 title text size
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 30
BUTTON_RADIUS = 4

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (88, 94, 149)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)

class BomberManApp:
    def __init__(self):
        pygame.init()

        # Set up screen and fonts
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.h1_font = pygame.font.Font(None, H1_SIZE)

        pygame.display.set_caption("BomberMan")

        # Set up title and background image
        self.title_text = self.h1_font.render("BOMBER-MAN", True, BLACK)
        self.bg_image = pygame.transform.scale(pygame.image.load("photos/bg.jpg"), (WIDTH, HEIGHT))  # Scale image to fit the screen

        # Set up buttons
        self.singleplayer_button = Button(WIDTH // 2 - BUTTON_WIDTH - 20, HEIGHT // 2 - BUTTON_HEIGHT // 2, BUTTON_WIDTH, BUTTON_HEIGHT,
                                          "Singleplayer")
        self.multiplayer_button = Button(WIDTH // 2 + 20, HEIGHT // 2 - BUTTON_HEIGHT // 2, BUTTON_WIDTH, BUTTON_HEIGHT, "Multiplayer")

        # When initialing the class
        self.running = False

    def draw_screen(self):
        # Fill screen with background image
        self.screen.blit(self.bg_image, (0, 0))  # Draw the background image

        # Draw the title text (H1 size)
        title_rect = self.title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        self.screen.blit(self.title_text, title_rect)

        # Draw the buttons
        self.singleplayer_button.draw(self.screen)
        self.multiplayer_button.draw(self.screen)

    def run(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                self.event_handler(event)

            self.draw_screen()

            # Update the display
            pygame.display.flip()

        # Quit if event handler returns self.running = False
        pygame.quit()

    def event_handler(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False

        if self.singleplayer_button.is_clicked():
            pygame.quit()  # Close menu
            subprocess.run(["python", "Player.py"])
        if self.multiplayer_button.is_clicked():
            print("Button clicked: Multiplayer")


# Define Button class
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.action = action

    def draw(self, screen):
        # Change button color on hover
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, BUTTON_HOVER_COLOR, self.rect, border_radius=BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=BUTTON_RADIUS)

        # Render the text on the button
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        # Check if the button is clicked
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False

if __name__ == '__main__':
    app = BomberManApp()
    app.run()