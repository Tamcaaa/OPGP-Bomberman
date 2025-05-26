import config
import os
import pygame

from managers.state_manager import StateManager


class BomberManApp:
    def __init__(self):
        pygame.init()  # Initialize Pygame
        pygame.mixer.init()

        self.game_canvas = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.h1_font = pygame.font.Font(None, config.H1_SIZE)
        self.state_stack = []
        self.dt, self.prev_time = 0, 0
        self.running = False
        self.photos_dir = os.path.join("assets")

        self.state_manager = StateManager(self)

        self.load_states()  # Load initial states

        self.all_sprites = pygame.sprite.Group()
        self.settings = {
            "volume": 0.5,
        }

    def run(self):
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            clock.tick(60)  # FPS limit
            self.get_events()  # Handle input events
            self.update()
            self.render()  # Render current state

    def update(self):
        current_stack = self.state_stack[-1]
        current_stack.update()

    def render(self):
        """Render the game state."""
        self.state_stack[-1].render(self.game_canvas)
        self.screen.blit(self.game_canvas, (0, 0))
        pygame.display.flip()

    def load_states(self):
        """Load the MainMenu state."""
        self.state_manager.change_state("MainMenu")

    def get_events(self):
        """Handle events like window close or key presses."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

            if self.state_stack:
                self.state_stack[-1].handle_events(event)

    def draw_text(self, screen: pygame.Surface, text: str, color: pygame.Color | tuple, x: int, y: int):
        """Render text on the screen."""
        text_surface = self.h1_font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        screen.blit(text_surface, text_rect)


# Start the game
if __name__ == '__main__':
    app = BomberManApp()
    app.run()
    pygame.quit()