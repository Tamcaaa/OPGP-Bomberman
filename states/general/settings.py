import pygame
import config
import os
from states.general.state import State
from custom_classes.button import Button


class Settings(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Settings")
        self.font = pygame.font.Font(None, config.FONT_SIZE)

        self.volume = game.settings.get("volume", 0.5)
        self.last_volume = self.volume if self.volume > 0.0 else 0.5

        # Load background image like PauseState
        self.background_image = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(),
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )

        # Load sound icons
        self.sound_on_img = pygame.image.load("assets/not_muted.png").convert_alpha()
        self.sound_off_img = pygame.image.load("assets/mute.png").convert_alpha()
        self.sound_on_img = pygame.transform.scale(self.sound_on_img, (20, 20))
        self.sound_off_img = pygame.transform.scale(self.sound_off_img, (20, 20))

        # Key binding settings
        self.key_bindings = {
            "player1": list(config.PLAYER1_MOVE_KEYS),
            "player2": list(config.PLAYER2_MOVE_KEYS)
        }
        self.editing_key = None
        self.editing_player = None
        self.editing_action = None

        # Buttons with PauseState style
        self.back_button = Button(20, config.SCREEN_HEIGHT - 70, 150, 50, "Back",
                                  font='CaveatBrush-Regular.ttf',
                                  button_color=config.COLOR_BEIGE)

        # Mute button - keep icon, but wrap in Button for hover effect
        current_img = self.sound_on_img if self.volume > 0.0 else self.sound_off_img
        self.mute_button = IconButton(385, 442, 40, 40, current_img)

        # Volume slider setup
        self.slider_x = 450
        self.slider_y = 460
        self.slider_width = 120
        self.slider_height = 8
        self.slider_handle_radius = 6

        # Key binding buttons with PauseState Button style
        self.key_bind_buttons = {}
        actions = ["Up", "Left", "Down", "Right", "Bomb"]
        start_x_p1 = 250
        start_x_p2 = 500
        start_y = 140
        button_width = 200
        button_height = 40
        spacing = 50

        for i, action in enumerate(actions):
            y = start_y + i * spacing

            btn_p1 = Button(
                start_x_p1, y, button_width, button_height,
                f"P1 {action}: {pygame.key.name(self.key_bindings['player1'][i])}",
                font='CaveatBrush-Regular.ttf',
                button_color=config.COLOR_BEIGE
            )
            self.key_bind_buttons[f"player1_{i}"] = btn_p1

            btn_p2 = Button(
                start_x_p2, y, button_width, button_height,
                f"P2 {action}: {pygame.key.name(self.key_bindings['player2'][i])}",
                font='CaveatBrush-Regular.ttf',
                button_color=config.COLOR_BEIGE
            )
            self.key_bind_buttons[f"player2_{i}"] = btn_p2

    def handle_events(self, event):
        if self.editing_key is not None:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    self.key_bindings[self.editing_player][self.editing_action] = event.key
                    btn_key = f"{self.editing_player}_{self.editing_action}"
                    action_name = ["Up", "Left", "Down", "Right", "Bomb"][self.editing_action]
                    self.key_bind_buttons[btn_key].text = (
                        f"{'P1' if self.editing_player == 'player1' else 'P2'} "
                        f"{action_name}: {pygame.key.name(event.key)}"
                    )
                    self.update_player_config()

                self.editing_key = None
                self.editing_player = None
                self.editing_action = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked():
                self.exit_state()
            elif self.mute_button.is_clicked():
                self.toggle_mute()
            else:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if (self.slider_y <= mouse_y <= self.slider_y + self.slider_height and
                        self.slider_x <= mouse_x <= self.slider_x + self.slider_width):
                    self.set_volume_from_slider(mouse_x)
                else:
                    for btn_key, button in self.key_bind_buttons.items():
                        if button.is_clicked():
                            parts = btn_key.split("_")
                            self.editing_player = parts[0]
                            self.editing_action = int(parts[1])
                            self.editing_key = btn_key
                            button.text = "Press any key..."
                            break

        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                mouse_x, _ = pygame.mouse.get_pos()
                if self.slider_x <= mouse_x <= self.slider_x + self.slider_width:
                    self.set_volume_from_slider(mouse_x)

    def set_volume_from_slider(self, mouse_x):
        rel_x = mouse_x - self.slider_x
        self.volume = max(0.0, min(1.0, rel_x / self.slider_width))
        if self.volume > 0.0:
            self.last_volume = self.volume
            self.mute_button.image = self.sound_on_img
        else:
            self.mute_button.image = self.sound_off_img
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def toggle_mute(self):
        if self.volume > 0.0:
            self.last_volume = self.volume
            self.volume = 0.0
            self.mute_button.image = self.sound_off_img
        else:
            self.volume = self.last_volume
            self.mute_button.image = self.sound_on_img
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def update_player_config(self):
        config.PLAYER1_MOVE_KEYS[:] = self.key_bindings["player1"]
        config.PLAYER2_MOVE_KEYS[:] = self.key_bindings["player2"]
        config.PLAYER_CONFIG[1]['move_keys'] = config.PLAYER1_MOVE_KEYS
        config.PLAYER_CONFIG[2]['move_keys'] = config.PLAYER2_MOVE_KEYS

    def render(self, screen):
        # Draw background image for consistent style
        screen.blit(self.background_image, (0, 0))

        # Draw buttons with hover effect
        self.back_button.draw(screen)
        self.mute_button.draw(screen)

        # Draw volume slider
        pygame.draw.rect(screen, (200, 200, 200), (self.slider_x, self.slider_y, self.slider_width, self.slider_height))
        filled_width = int(self.volume * self.slider_width)
        pygame.draw.rect(screen, (255, 0, 0), (self.slider_x, self.slider_y, filled_width, self.slider_height))
        handle_x = self.slider_x + filled_width
        pygame.draw.circle(screen, (255, 0, 0), (handle_x, self.slider_y + self.slider_height // 2), self.slider_handle_radius)

        # Volume label
        vol_text = self.font.render(f"Volume: {int(self.volume * 100)}%", True, config.COLOR_BEIGE)
        screen.blit(vol_text, (self.slider_x, self.slider_y - 30))

        # Draw key binding buttons with hover highlight
        for button in self.key_bind_buttons.values():
            button.draw(screen)

        # Key bindings labels
        bindings_title_font = pygame.font.Font(None, 60) 
        bindings_title = bindings_title_font.render("Key Bindings", True, config.TEXT_COLOR)
        screen.blit(bindings_title, (350, 40))
        
        screen.blit(self.font.render("Player 1", True, config.TEXT_COLOR), (320, 110))
        screen.blit(self.font.render("Player 2", True, config.TEXT_COLOR), (570, 110))

        # If editing key, show instruction text
        if self.editing_key is not None:
            action_names = ["Up", "Left", "Down", "Right", "Bomb"]
            editing_text = self.font.render(
                f"Press key for P{1 if self.editing_player == 'player1' else 2} "
                f"{action_names[self.editing_action]}",
                True, config.COLOR_GREEN
            )
            screen.blit(editing_text, (500, 400))

# IconButton for mute toggle, wraps an image with hover effect rectangle
class IconButton:
    def __init__(self, x, y, width, height, image):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = image
        self.highlighted = False

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = config.BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) or self.highlighted else config.COLOR_BEIGE
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)
        # Center the image inside the button rect
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect)

    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
