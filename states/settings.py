import pygame
import config
from states.state import State


class Settings(State):
    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Settings")
        self.font = pygame.font.Font(None, config.FONT_SIZE)

        self.volume = game.settings.get("volume", 0.5)
        self.last_volume = self.volume if self.volume > 0.0 else 0.5

        # Načítanie ikoniek
        self.sound_on_img = pygame.image.load("assets/not_muted.png").convert_alpha()
        self.sound_off_img = pygame.image.load("assets/mute.png").convert_alpha()

        # Môžeš si zmeniť veľkosť ikonky, ak treba
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

        # Buttons
        self.back_button = Button(20, config.SCREEN_HEIGHT - 70, 150, 50, "Back")

        # Tlačidlo zvuku teraz s obrázkom
        current_img = self.sound_on_img if self.volume > 0.0 else self.sound_off_img
        self.mute_button = Button(385, 442, 40, 40, image=current_img)

        # Volume slider
        self.slider_x = 420
        self.slider_y = 450
        self.slider_width = 120
        self.slider_height = 8
        self.slider_handle_radius = 6

        # Key binding buttons
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
        
            # Player 1 buttons (zarovnané vľavo)
            btn_p1 = Button(
                start_x_p1, y, button_width, button_height,
                f"P1 {action}: {pygame.key.name(self.key_bindings['player1'][i])}"
            )
            self.key_bind_buttons[f"player1_{i}"] = btn_p1
        
            # Player 2 buttons (zarovnané vpravo)
            btn_p2 = Button(
                start_x_p2, y, button_width, button_height,
                f"P2 {action}: {pygame.key.name(self.key_bindings['player2'][i])}"
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
                # Check if slider clicked
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
        screen.fill((30, 30, 30))

        # Buttons
        self.back_button.draw(screen)
        self.mute_button.draw(screen)

        # Volume slider
        pygame.draw.rect(screen, (200, 200, 200), (self.slider_x, self.slider_y, self.slider_width, self.slider_height))
        filled_width = int(self.volume * self.slider_width)
        pygame.draw.rect(screen, (255, 0, 0), (self.slider_x, self.slider_y, filled_width, self.slider_height))
        handle_x = self.slider_x + filled_width
        pygame.draw.circle(screen, (255, 0, 0), (handle_x, self.slider_y + self.slider_height // 2), self.slider_handle_radius)

        # Volume label
        vol_text = self.font.render(f"Volume: {int(self.volume * 100)}%", True, config.TEXT_COLOR)
        screen.blit(vol_text, (self.slider_x, self.slider_y - 30))

        # Key binding buttons
        for button in self.key_bind_buttons.values():
            button.draw(screen)

        # Key bindings labels
        bindings_title = self.font.render("Key Bindings", True, config.TEXT_COLOR)
        screen.blit(bindings_title, (420, 40))
        screen.blit(self.font.render("Player 1", True, config.TEXT_COLOR), (300, 80))
        screen.blit(self.font.render("Player 2", True, config.TEXT_COLOR), (550, 80))

        if self.editing_key is not None:
            action_names = ["Up", "Left", "Down", "Right", "Bomb"]
            editing_text = self.font.render(
                f"Press key for P{1 if self.editing_player == 'player1' else 2} "
                f"{action_names[self.editing_action]}",
                True, config.COLOR_GREEN
            )
            screen.blit(editing_text, (500, 400))


class Button:
    def __init__(self, x, y, width=None, height=None, text=None, image=None):
        self.text = text
        self.image = image
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        
        if self.image:
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        elif self.text:
            text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
            screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]
