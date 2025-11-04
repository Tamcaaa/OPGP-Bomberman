import pygame
import config

class Button:
    def __init__(self, x, y, width, height, text, action=None,font=None,
                 font_size=config.FONT_SIZE,
                 button_color=config.BUTTON_COLOR,
                 button_hover_color=config.BUTTON_HOVER_COLOR,
                 button_radius=config.BUTTON_RADIUS,):
        """Initialize button with position, size, and text."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(font, font_size)
        self.action = action
        self.button_color = button_color
        self.button_hover_color = button_hover_color
        self.button_radius = button_radius

    def draw(self, screen):
        """Draw the button on screen."""
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, self.button_hover_color, self.rect, border_radius=self.button_radius)
        else:
            pygame.draw.rect(screen, self.button_color, self.rect, border_radius=self.button_radius)

        # Render the text on the button
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        """Check if the button is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]