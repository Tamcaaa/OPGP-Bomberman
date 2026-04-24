import pygame
import config

class Button:
    def __init__(self, x, y, width, height, text, action=None, font=None,
                 font_size=22,
                 button_color=None,
                 button_hover_color=None,
                 button_radius=12,
                 style="outline"):  # style: "outline" | "filled"
        self.rect   = pygame.Rect(x, y, width, height)
        self.text   = text
        self.font   = pygame.font.Font(font or "CaveatBrush-Regular.ttf", font_size)
        self.action = action
        self.radius = button_radius
        self.style  = style

        # Farby podľa štýlu
        if style == "filled":
            self.color       = button_color       or config.BTN_BEIGE
            self.hover_color = button_hover_color or (225, 200, 160)
            self.text_color  = config.BG_BASE
        else:
            self.color       = button_color       or config.BG_PANEL
            self.hover_color = button_hover_color or (15, 17, 26)
            self.text_color  = config.TEXT_PRIMARY

        self.visible = True
        self.enabled = True

    def draw(self, screen):
        if not self.visible:
            return

        hovered = self.rect.collidepoint(pygame.mouse.get_pos()) and self.enabled
        bg      = self.hover_color if hovered else self.color

        # Podklad
        pygame.draw.rect(screen, bg, self.rect, border_radius=self.radius)

        # Orámovanie
        if self.style == "outline":
            border_col = (20, 22, 35) if hovered else config.BORDER_SUBTLE
            pygame.draw.rect(screen, border_col, self.rect, width=1, border_radius=self.radius)
        else:
            pygame.draw.rect(screen, (225, 200, 160), self.rect, width=1, border_radius=self.radius)

        # Text so shadow
        shadow = self.font.render(self.text, True, (0, 0, 0))
        label  = self.font.render(self.text, True, self.text_color)
        cx = self.rect.centerx - label.get_width() // 2
        cy = self.rect.centery - label.get_height() // 2
        screen.blit(shadow, (cx + 1, cy + 1))
        screen.blit(label,  (cx, cy))

    def is_clicked(self, event=None):
        """
        Volaj s eventom z handle_events():
            if self.btn.is_clicked(event): ...

        Reaguje na MOUSEBUTTONDOWN (myš / touchpad) aj FINGERDOWN (macOS touch).
        """
        if not (self.visible and self.enabled):
            return False

        if event is not None:
            # Štandardný klik myšou / touchpadom
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.rect.collidepoint(event.pos)

            # macOS FINGERDOWN – súradnice sú normalizované 0.0–1.0
            if event.type == pygame.FINGERDOWN:
                surf = pygame.display.get_surface()
                fx = int(event.x * surf.get_width())
                fy = int(event.y * surf.get_height())
                return self.rect.collidepoint(fx, fy)

            return False

        return (self.rect.collidepoint(pygame.mouse.get_pos())
                and pygame.mouse.get_pressed()[0])

    def set_visible(self, visible: bool):
        self.visible = visible

    def set_enabled(self, enabled: bool):
        self.enabled = enabled