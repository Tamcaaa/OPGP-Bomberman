import pygame
from states.state import State
import config
from managers.state_manager import StateManager

AVAILABLE_COLORS = ["red", "blue", "green", "yellow", "white", "black"]

class ColorSelector(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Color Selection")
        self.state_manager = StateManager(self.game)

        # Player color storage
        self.players = {1: None, 2: None}  
        self.taken_colors = []

        # UI setup
        self.font = pygame.font.SysFont("Arial", 28)
        self.instruction_font = pygame.font.SysFont("Arial", 22)
        self.selected_index = {1: 0, 2: 0}
        self.current_player = 1

    def draw(self, screen):
        screen.fill((20, 20, 30))
        y = 100
        spacing = 70

        for idx, color in enumerate(AVAILABLE_COLORS):
            rect = pygame.Rect(200, y, 200, 50)
            
            # grey out taken colors
            if color in self.taken_colors:
                pygame.draw.rect(screen, (80, 80, 80), rect)
            else:
                pygame.draw.rect(screen, pygame.Color(color), rect)

            # highlight current selection
            if idx == self.selected_index[self.current_player]:
                border_color = (255, 255, 255)
                pygame.draw.rect(screen, border_color, rect, 3)

            # color name
            text_color = (255, 255, 255) if color not in self.taken_colors else (150, 150, 150)
            text = self.font.render(color.upper(), True, text_color)
            screen.blit(text, (rect.x + 10, rect.y + 10))
            y += spacing

        instr = f"Player {self.current_player}: Use ↑ ↓ to move, ENTER to select"
        screen.blit(self.instruction_font.render(instr, True, (255, 255, 0)), (50, 20))
        pygame.display.flip()

    def handle_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        idx = self.selected_index[self.current_player]

        # Move selection
        if event.key == pygame.K_UP:
            idx = (idx - 1) % len(AVAILABLE_COLORS)
        elif event.key == pygame.K_DOWN:
            idx = (idx + 1) % len(AVAILABLE_COLORS)
        self.selected_index[self.current_player] = idx

        # Confirm selection
        if event.key == pygame.K_RETURN:
            chosen = AVAILABLE_COLORS[idx]
            if chosen not in self.taken_colors:
                self.players[self.current_player] = chosen
                self.taken_colors.append(chosen)

                if self.current_player == 1:
                    # Switch to player 2
                    self.current_player = 2
                    # Skip colors already taken
                    while AVAILABLE_COLORS[self.selected_index[self.current_player]] in self.taken_colors:
                        self.selected_index[self.current_player] = (self.selected_index[self.current_player] + 1) % len(AVAILABLE_COLORS)
                else:
                    # Both players have chosen → go to MapSelector
                    from states.map_selector import MapSelector
                    self.state_manager.change_state(
                        "MapSelector",
                        player_colors=self.players  # pass chosen colors
                    )
