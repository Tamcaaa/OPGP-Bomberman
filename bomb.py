import pygame
import config
import time

class Bomb(pygame.sprite.Sprite):
    def __init__(self, player, bomb_group):
        super().__init__()
        self.image = pygame.image.load("photos/bomb.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (config.GRID_SIZE, config.GRID_SIZE))
        self.rect = self.image.get_rect()
        self.rect.topleft = player.rect.topleft  # Položenie bomby na hráčovu pozíciu
        
        self.range = player.power
        self.player = player
        self.fuse_time = time.time() + 3  # Bomba vybuchne po 3 sekundách
        
        bomb_group.add(self)  # Pridanie bomby do skupiny
    
    def update(self, bomb_group):
        if time.time() >= self.fuse_time:
            self.explode(bomb_group)
    
    def explode(self, bomb_group):
        print("Bomba vybuchla!")  # Tu môžeme neskôr pridať animáciu výbuchu
        self.player.currentBomb += 1  # Hráč môže položiť ďalšiu bombu
        self.kill()  # Odstránenie bomby zo skupiny

