import pygame
import random
import config
import time
import os  # Import os directly


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type=None):
        super().__init__()

        # If no specific type is provided, randomly choose one
        if powerup_type is None:
            self.type = random.choice([
                "bomb_powerup",  # Increases max bombs
                "speed_powerup",  # Increases explosion range
                "freeze_powerup",  # Freezes the other player
                "live+_powerup",  # Adds an extra life
                "apple_powerup"  # Temporary invincibility
            ])
        else:
            self.type = powerup_type

        # Load image based on powerup type or create a fallback
        try:
            image_path = f"assets/power_ups/{self.type}.png"
            # Try to load the image, but if the file doesn't exist, create a fallback
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (config.GRID_SIZE, config.GRID_SIZE))
            else:
                self.image = self.create_fallback_image()
        except (pygame.error, FileNotFoundError):
            # If loading fails for any reason, use a fallback image
            self.image = self.create_fallback_image()

        # Position the power-up
        self.rect = self.image.get_rect()
        self.rect.x = x * config.GRID_SIZE
        self.rect.y = y * config.GRID_SIZE

        # Set power-up properties
        self.reveal_time = time.time()
        self.field_duration = 30  # Power-up remains on the field for 30 seconds
        self.collected = False
        self.effect_duration = 30  # Duration of effect in seconds after collection
        self.hidden = True  # Start as hidden under a brick
        self.frozen_until = 0

    def create_fallback_image(self):
        """Create a colored rectangle as fallback for missing images"""
        image = pygame.Surface((config.GRID_SIZE, config.GRID_SIZE))

        # Different colors for different power-up types
        if self.type == "bomb_powerup":
            image.fill((255, 0, 0))  # Red for bomb power
        elif self.type == "speed_powerup":
            image.fill((0, 0, 255))  # Blue for speed/range
        elif self.type == "freeze_powerup":
            image.fill((0, 255, 255))  # Cyan for freeze
        elif self.type == "live+_powerup":
            image.fill((0, 255, 0))  # Green for extra life
        elif self.type == "apple_powerup":
            image.fill((255, 255, 0))  # Yellow for invincibility
        else:
            image.fill((150, 150, 150))  # Gray for unknown types

        # Draw a symbol on the surface to indicate the power-up type
        font = pygame.font.Font(None, 24)

        # First letter of the power-up type as symbol
        symbol = self.type[0].upper()
        text = font.render(symbol, True, (0, 0, 0))
        text_rect = text.get_rect(center=(config.GRID_SIZE // 2, config.GRID_SIZE // 2))

        image.blit(text, text_rect)
        return image

    def update(self):
        """Check if the power-up should disappear due to time limit"""
        # Only visible power-ups should expire
        if not self.hidden and not self.collected and time.time() - self.reveal_time > self.field_duration:
            self.kill()  # Remove power-up if it's been on the field too long

    def reveal(self):
        """Reveal the power-up when the brick hiding it is destroyed"""
        self.hidden = False
        self.reveal_time = time.time()  # Reset timer when revealed

    def apply_effect(self, player):
        """Apply the power-up effect to the player who collected it"""
        self.collected = True
        if self.type == "bomb_powerup":
            if player.maxBombs < player.max_bomb_limit:  # optional limit if you want
                player.activate_powerup("bomb_powerup")
            return f"Player {player.player_id} can place more bombs permanently!"

        elif self.type == "speed_powerup":
            player.activate_powerup('speed_powerup')
            return f"Player {player.player_id}'s explosion range increased for {self.effect_duration}s!"

        elif self.type == "freeze_powerup":
            # Apply freeze effect to the other player
            player.activate_powerup("freeze_powerup", 5)
            return f"Player {player.player_id} froze the opponent for 5s!"

        elif self.type == "live+_powerup":
            player.activate_powerup("live+_powerup")
            return f"Player {player.player_id} gained an extra life!"

        elif self.type == "apple_powerup":
            # Temporary invincibility
            player.activate_powerup("apple_powerup")
            return f"Player {player.player_id} is invincible for {self.effect_duration}s!"

        return f"Player {player.player_id} collected a power-up!"
