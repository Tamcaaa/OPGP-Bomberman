import random
import pygame
import config


class PowerUpManager:
    def __init__(self):
        self.types = [
            "bomb_powerup",  # Increases max bombs
            "speed_powerup",  # Increases explosion range
            "freeze_powerup",  # Freezes the other player
            "live+_powerup",  # Adds an extra life
            "apple_powerup"  # Temporary invincibility
        ]
        self.powers = []

    def spawn_power_up(self, x, y, power_type=None):
        if not power_type:
            power_type = random.choice(self.types)
        image_path = f"assets/power_ups/{power_type}.png"
        image = pygame.image.load(image_path).convert_alpha()
        image = pygame.transform.scale(image, (config.GRID_SIZE, config.GRID_SIZE))

        rect = image.get_rect()
        rect.x = x * config.GRID_SIZE
        rect.y = y * config.GRID_SIZE

        self.powers.append((rect, power_type, image))

    def get_power_ups(self) -> list:
        return self.powers
    def hande_power_up(self):
        pass
