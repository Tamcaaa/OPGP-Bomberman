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
        self.volume_up_button = Button(330, 200, 50, 50, "+")
        self.volume_down_button = Button(220, 200, 50, 50, "-")
        self.mute_button = Button(220, 300, 150, 50, "Mute" if self.volume > 0.0 else "Unmute")

        # Key binding buttons
        self.key_bind_buttons = {}
        actions = ["Up", "Left", "Down", "Right", "Bomb"]
        for i, action in enumerate(actions):
            # Player 1 buttons
            btn = Button(
                500, 100 + i * 50, 200, 40,
                f"P1 {action}: {pygame.key.name(self.key_bindings['player1'][i])}"
            )
            self.key_bind_buttons[f"player1_{i}"] = btn

            # Player 2 buttons
            btn = Button(
                750, 100 + i * 50, 200, 40,
                f"P2 {action}: {pygame.key.name(self.key_bindings['player2'][i])}"
            )
            self.key_bind_buttons[f"player2_{i}"] = btn

    def handle_events(self, event):
        if self.editing_key is not None:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:  # Don't allow escape to be bound
                    # Update the key binding
                    self.key_bindings[self.editing_player][self.editing_action] = event.key

                    # Update the button text
                    btn_key = f"{self.editing_player}_{self.editing_action}"
                    action_name = ["Up", "Left", "Down", "Right", "Bomb"][self.editing_action]
                    self.key_bind_buttons[btn_key].text = (
                        f"{'P1' if self.editing_player == 'player1' else 'P2'} "
                        f"{action_name}: {pygame.key.name(event.key)}"
                    )

                    # Update the config
                    self.update_player_config()

                self.editing_key = None
                self.editing_player = None
                self.editing_action = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked():
                self.exit_state()
            elif self.volume_up_button.is_clicked():
                self.adjust_volume(0.1)
            elif self.volume_down_button.is_clicked():
                self.adjust_volume(-0.1)
            elif self.mute_button.is_clicked():
                self.toggle_mute()
            else:
                # Check key binding buttons
                for btn_key, button in self.key_bind_buttons.items():
                    if button.is_clicked():
                        parts = btn_key.split("_")
                        self.editing_player = parts[0]
                        self.editing_action = int(parts[1])
                        self.editing_key = btn_key
                        button.text = "Press any key..."
                        break

    def adjust_volume(self, change):
        self.volume = max(0.0, min(1.0, self.volume + change))
        if self.volume > 0.0:
            self.last_volume = self.volume
            self.mute_button.text = "Mute"
        else:
            self.mute_button.text = "Unmute"
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def toggle_mute(self):
        if self.volume > 0.0:
            self.last_volume = self.volume
            self.volume = 0.0
            self.mute_button.text = "Unmute"
        else:
            self.volume = self.last_volume
            self.mute_button.text = "Mute"
        pygame.mixer.music.set_volume(self.volume)
        self.game.settings["volume"] = self.volume

    def update_player_config(self):
        """Update the player config with the new key bindings"""
        config.PLAYER1_MOVE_KEYS[:] = self.key_bindings["player1"]
        config.PLAYER2_MOVE_KEYS[:] = self.key_bindings["player2"]

        # Update the PLAYER_CONFIG dictionary
        config.PLAYER_CONFIG[1]['move_keys'] = config.PLAYER1_MOVE_KEYS
        config.PLAYER_CONFIG[2]['move_keys'] = config.PLAYER2_MOVE_KEYS

    def render(self, screen):
        screen.fill((30, 30, 30))

        # Draw buttons
        self.back_button.draw(screen)
        self.volume_up_button.draw(screen)
        self.volume_down_button.draw(screen)
        self.mute_button.draw(screen)

        # Draw key binding buttons
        for button in self.key_bind_buttons.values():
            button.draw(screen)

        # Volume text
        vol_text = self.font.render(f"Volume: {int(self.volume * 100)}%", True, config.TEXT_COLOR)
        screen.blit(vol_text, (200, 150))

        # Key bindings title
        bindings_title = self.font.render("Key Bindings", True, config.TEXT_COLOR)
        screen.blit(bindings_title, (600, 50))

        # Player labels
        player1_label = self.font.render("Player 1", True, config.TEXT_COLOR)
        player2_label = self.font.render("Player 2", True, config.TEXT_COLOR)
        screen.blit(player1_label, (500, 70))
        screen.blit(player2_label, (750, 70))

        # Editing indicator
        if self.editing_key is not None:
            action_names = ["Up", "Left", "Down", "Right", "Bomb"]
            editing_text = self.font.render(
                f"Press key for P{1 if self.editing_player == 'player1' else 2} "
                f"{action_names[self.editing_action]}",
                True, config.COLOR_GREEN
            )
            screen.blit(editing_text, (500, 400))

        # Mute status text
        if self.volume == 0.0:
            mute_text = self.font.render("Sound Muted", True, config.TEXT_COLOR)
            screen.blit(mute_text, (config.SCREEN_WIDTH // 2, 350))


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = config.BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=config.BUTTON_RADIUS)
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]
