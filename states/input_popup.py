import pygame
import config
from states.state import State
from managers.state_manager import StateManager


class InputPopup(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: Test")
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.active_box = None  # Track which box is active: 'username' or 'address'

        self.state_manager = StateManager(game)

        # Input boxes setup
        self.username_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3, config.SCREEN_WIDTH // 2, 40)
        self.address_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3 + 80, config.SCREEN_WIDTH // 2, 40)

        self.username_text = ""
        self.address_text = ""

        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')

        self.username_color = self.color_inactive
        self.address_color = self.color_inactive

        self.result = None  # Will hold tuple (username, address)

        # Create a submit button rect
        self.submit_rect = pygame.Rect(config.SCREEN_WIDTH // 2 - 50, config.SCREEN_HEIGHT // 3 + 150, 100, 40)
        self.submit_color = pygame.Color('gray')

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.username_rect.collidepoint(event.pos):
                self.active_box = 'username'
                self.username_color = self.color_active
                self.address_color = self.color_inactive
            elif self.address_rect.collidepoint(event.pos):
                self.active_box = 'address'
                self.address_color = self.color_active
                self.username_color = self.color_inactive
            elif self.submit_rect.collidepoint(event.pos):
                if self.username_text.strip() and self.address_text.strip():
                    self.result = (self.username_text.strip(), self.address_text.strip())
                    self.exit_state()
                    self.state_manager.change_state("MultiplayerLobby", False, *self.result)
            else:
                # Clicked outside any box: deactivate
                self.active_box = None
                self.username_color = self.color_inactive
                self.address_color = self.color_inactive

        if event.type == pygame.KEYDOWN and self.active_box:
            if event.key == pygame.K_RETURN:
                if self.username_text.strip() and self.address_text.strip():
                    self.result = (self.username_text.strip(), self.address_text.strip())
                    self.exit_state()
                    self.state_manager.change_state("MultiplayerLobby", False, *self.result)
            elif event.key == pygame.K_BACKSPACE:
                if self.active_box == 'username':
                    self.username_text = self.username_text[:-1]
                else:
                    self.address_text = self.address_text[:-1]
            else:
                if self.active_box == 'username':
                    self.username_text += event.unicode
                else:
                    self.address_text += event.unicode

    def render(self, screen):
        # Draw popup background
        popup_rect = pygame.Rect(config.SCREEN_WIDTH // 4 - 10, config.SCREEN_HEIGHT // 3 - 20, config.SCREEN_WIDTH // 2 + 20, 220)
        pygame.draw.rect(screen, (50, 50, 50), popup_rect, border_radius=8)

        # Draw labels
        username_label = self.font.render("Username:", True, config.TEXT_COLOR)
        address_label = self.font.render("Host Address:", True, config.TEXT_COLOR)
        screen.blit(username_label, (self.username_rect.x, self.username_rect.y - 25))
        screen.blit(address_label, (self.address_rect.x, self.address_rect.y - 25))

        # Draw input boxes
        pygame.draw.rect(screen, self.username_color, self.username_rect, 2, border_radius=5)
        pygame.draw.rect(screen, self.address_color, self.address_rect, 2, border_radius=5)

        # Draw input text
        username_surface = self.font.render(self.username_text, True, config.TEXT_COLOR)
        address_surface = self.font.render(self.address_text, True, config.TEXT_COLOR)
        screen.blit(username_surface, (self.username_rect.x + 5, self.username_rect.y + 8))
        screen.blit(address_surface, (self.address_rect.x + 5, self.address_rect.y + 8))

        # Draw submit button
        pygame.draw.rect(screen, self.submit_color, self.submit_rect, border_radius=5)
        submit_text = self.font.render("Join", True, (255, 255, 255))
        submit_rect = submit_text.get_rect(center=self.submit_rect.center)
        screen.blit(submit_text, submit_rect)
