import time, os, pygame, config
from states.main_menu import MainMenu  # Import MainMenu state


class BomberManApp:
    def __init__(self):
        pygame.init()  # Initialize Pygame
        self.game_canvas = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.h1_font = pygame.font.Font(None, config.H1_SIZE)
        self.state_stack = []
        self.dt, self.prev_time = 0, time.time()  # Initialize with current time
        self.running = False
        self.photos_dir = os.path.join("photos")
        self.load_states()  # Load initial states

        self.all_sprites = pygame.sprite.Group()
        self.player1 = None
        self.player2 = None

    def run(self):
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            self.get_dt()  # Update delta time
            self.get_events()  # Handle input events
            self.render()  # Render current state
            clock.tick(120)  # FPS limit

    def get_dt(self):
        """Calculate delta time."""
        now = time.time()
        self.dt = now - self.prev_time
        self.prev_time = now

    def render(self):
        """Render the game state."""
        self.state_stack[-1].render(self.game_canvas)
        self.screen.blit(self.game_canvas, (0, 0))
        pygame.display.flip()

    def load_states(self):
        """Load the MainMenu state."""
        main_menu_screen = MainMenu(self)
        self.state_stack.append(main_menu_screen)

    def get_events(self):
        """Handle events like window close or key presses."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

            if self.state_stack:
                self.state_stack[-1].handle_events()

    def draw_text(self, screen: pygame.Surface, text: str, color: pygame.Color | tuple, x: int, y: int):
        """Render text on the screen."""
        text_surface = self.h1_font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        screen.blit(text_surface, text_rect)

    def check_for_death(self):
        """Check if either player has died and handle removal."""
        if self.player1 and self.player1.is_dead:
            self.player1 = None  # Remove player1 from the game
        if self.player2 and self.player2.is_dead:
            self.player2 = None  # Remove player2 from the game

        # If both players are dead, end the game
        if self.player1 is None and self.player2 is None:
            from states.game_over import GameOver
            new_state = GameOver(self)
            new_state.enter_state()


# Start the game
if __name__ == '__main__':
    app = BomberManApp()
    app.run()
    pygame.quit()