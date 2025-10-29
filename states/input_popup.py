import pygame
import config
from states.state import State
from managers.state_manager import StateManager


class InputPopup(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: Test")
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.active_box = None

        self.state_manager = StateManager(game)

        # Input boxes
        self.username_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3, config.SCREEN_WIDTH // 2, 40)
        self.address_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3 + 80, config.SCREEN_WIDTH // 2, 40)

        self.username_text = ""
        self.address_text = ""

        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')

        self.username_color = self.color_inactive
        self.address_color = self.color_inactive

        self.result = None

        # Buttons
        button_y = config.SCREEN_HEIGHT // 3 + 150
        self.join_button = Button(config.SCREEN_WIDTH // 2 + 10, button_y, 100, 40, "Join", self.submit)
        self.back_button = Button(config.SCREEN_WIDTH // 2 - 110, button_y, 100, 40, "Back", self.go_back)

    def submit(self):
        if self.username_text.strip() and self.address_text.strip():
            self.result = (self.username_text.strip(), self.address_text.strip())
            self.exit_state()
            self.state_manager.change_state("MultiplayerLobby",*self.result)

    def go_back(self):
        self.exit_state()

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
            else:
                self.active_box = None
                self.username_color = self.color_inactive
                self.address_color = self.color_inactive

        if event.type == pygame.KEYDOWN and self.active_box:
            if event.key == pygame.K_RETURN:
                self.submit()
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

        # Check button clicks
        if self.join_button.is_clicked():
            self.join_button.action()
        if self.back_button.is_clicked():
            self.back_button.action()

    def render(self, screen):
        popup_height = 260
        popup_rect = pygame.Rect(config.SCREEN_WIDTH // 4 - 10, config.SCREEN_HEIGHT // 3 - 20, config.SCREEN_WIDTH // 2 + 20, popup_height)
        pygame.draw.rect(screen, (50, 50, 50), popup_rect, border_radius=8)

        # Labels
        username_label = self.font.render("Username:", True, config.TEXT_COLOR)
        address_label = self.font.render("Host Address:", True, config.TEXT_COLOR)
        screen.blit(username_label, (self.username_rect.x, self.username_rect.y - 25))
        screen.blit(address_label, (self.address_rect.x, self.address_rect.y - 25))

        # Input boxes
        pygame.draw.rect(screen, self.username_color, self.username_rect, 2, border_radius=5)
        pygame.draw.rect(screen, self.address_color, self.address_rect, 2, border_radius=5)

        username_surface = self.font.render(self.username_text, True, config.TEXT_COLOR)
        address_surface = self.font.render(self.address_text, True, config.TEXT_COLOR)
        screen.blit(username_surface, (self.username_rect.x + 5, self.username_rect.y + 8))
        screen.blit(address_surface, (self.address_rect.x + 5, self.address_rect.y + 8))

        # Draw buttons
        self.join_button.draw(screen)
        self.back_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, config.BUTTON_HOVER_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, config.BUTTON_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
