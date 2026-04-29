import pygame
import random
import config
import time
import os

from game_objects.singleplayer import player 


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type=None):
        super().__init__()

        # ak obrázok nie je k dispozícií vyberie náhodný
        if powerup_type is None:
            self.type = random.choice([
                "bomb_powerup",  # zvýši počet bomb
                "range_powerup",  # zvýši dosah výbuchu
                "freeze_powerup",  # zmrazí/spomalí druhého hráča
                "live+_powerup",  # pridá extra život
                "shield_powerup",  # dočasná nezraniteľnosť
                "darkness_powerup"  # zníži viditeľnosť druhého hráča
            ])
        else:
            self.type = powerup_type

        # načítaj obrázok pre každý typ power-upu, pokiaľ existuje, inak fallback
        try:
            image_path = f"assets/power_ups/{self.type}.png"
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (25, 25))
            else:
                self.image = self.create_fallback_image()
        except (pygame.error, FileNotFoundError):
            self.image = self.create_fallback_image()

        # pozícia pre power-up
        self.rect = self.image.get_rect()
        self.rect.x = x * config.GRID_SIZE
        self.rect.y = y * config.GRID_SIZE

        # nastav vlastnosti pre efekty a časovače
        self.reveal_time = time.time()
        self.field_duration = config.FIELD_DURATION  # power-up sa objaví na určitý čas po zničení tehly
        self.collected = False
        self.effect_duration = config.EFFECT_DURATION
        self.hidden = True  
        self.frozen_until = config.FROZEN_UNTIL 

    def create_fallback_image(self):
        """Create a colored rectangle as fallback for missing images"""
        image = pygame.Surface((config.GRID_SIZE, config.GRID_SIZE))

        # Fallback farby
        if self.type == "bomb_powerup":
            image.fill((255, 0, 0))  # Červená pro bomb power
        elif self.type == "range_powerup":
            image.fill((0, 0, 255))  # Modrá pro range power
        elif self.type == "freeze_powerup":
            image.fill((0, 255, 255))  # Tyrkysová pre freeze power
        elif self.type == "live+_powerup":
            image.fill((0, 255, 0))  # Zelená pre live+ power
        elif self.type == "shield_powerup":
            image.fill((255, 255, 0))  # Žltá pre shield
        elif self.type == "darkness_powerup":
            image.fill((255, 0, 255))  # Magenta pre darkness
        else:
            image.fill((150, 150, 150))  # Sivá pre neznámé typy

        # Nakresli symbol pre každý typ power-upu
        font = pygame.font.Font(None, 24)

        # Prvé písmeno typu power-up jak symbol
        symbol = self.type[0].upper()
        text = font.render(symbol, True, (0, 0, 0))
        text_rect = text.get_rect(center=(config.GRID_SIZE // 2, config.GRID_SIZE // 2))

        image.blit(text, text_rect)
        return image

    def update(self):
        if not self.hidden:
            # odstráni sa po čase
            if time.time() - self.reveal_time > self.field_duration:
                self.kill()

    def reveal(self):
        """Reveal the power-up when the brick hiding it is destroyed"""
        self.hidden = False
        self.reveal_time = time.time()  # Reset časovač pre zobrazenie

    def apply_effect(self, player):
        """Apply the power-up effect to the player who collected it"""
        self.collected = True
        if self.type == "bomb_powerup":
            if player.maxBombs < player.max_bomb_limit:  # optional limit
                player.activate_powerup("bomb_powerup")
            return f"Player {player.player_id} can place more bombs permanently!"

        elif self.type == "range_powerup":
            player.activate_powerup('range_powerup')
            return f"Player {player.player_id}'s explosion range increased permanently!"

        elif self.type == "freeze_powerup":
            # nastav efekt zamrazenia na určitý čas
            freeze_duration = config.POWERUP_DURATIONS.get("freeze_powerup", 5)
            player.activate_powerup("freeze_powerup", freeze_duration)
            return f"Player {player.player_id} froze the opponent for {freeze_duration}s!"

        elif self.type == "live+_powerup":
            player.activate_powerup("live+_powerup")
            return f"Player {player.player_id} gained an extra life!"

        elif self.type == "shield_powerup":
            # čiastočná nezraniteľnosť na určitý čas
            shield_duration = config.POWERUP_DURATIONS.get("shield_powerup", 15)
            player.activate_powerup("shield_powerup", shield_duration)
            return f"Player {player.player_id} is invincible for {shield_duration}s!"

        elif self.type == "darkness_powerup":
            player.test_field.activate_darkness(15)
            return "Darkness falls!"
        return f"Player {player.player_id} collected a power-up!"