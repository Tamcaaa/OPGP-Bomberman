import pygame
import config

def load_images():
    images = {}
    
    # Backgrounds
    images['cave_bg'] = pygame.image.load("assets/cave-bg.png").convert_alpha()
    images['grass_bg'] = pygame.image.load("assets/grass-bg.png").convert_alpha()
    images['sand_bg'] = pygame.image.load("assets/sand-bg.png").convert_alpha()
    images['ruins_bg'] = pygame.image.load("assets/ruins_bg.png").convert_alpha()
    images['urban_bg'] = pygame.image.load("assets/urban_bg.png").convert_alpha()
    
    # Unbreakable and breakable tiles
    images['unbreakable_stone'] = pygame.transform.scale(pygame.image.load("assets/stone-black.png").convert_alpha(), (30, 30))
    images['breakable_barrel'] = pygame.transform.scale(pygame.image.load("assets/environment/barrel.png").convert_alpha(), (30, 30))
    images['breakable_bush'] = pygame.transform.scale(pygame.image.load("assets/environment/bush.png").convert_alpha(), (30, 30))
    images['unbreakable_rock'] = pygame.transform.scale(pygame.image.load("assets/environment/black-block-rock.png").convert_alpha(), (30, 30))
    images['breakable_rock'] = pygame.transform.scale(pygame.image.load("assets/environment/rock.png").convert_alpha(), (30, 30))
    images['breakable_diamond'] = pygame.transform.scale(pygame.image.load("assets/environment/diamond.png").convert_alpha(), (30, 30))
    images['breakable_cactus'] = pygame.transform.scale(pygame.image.load("assets/environment/cactus.png").convert_alpha(), (30, 30))
    images['unbreakable_box'] = pygame.transform.scale(pygame.image.load("assets/environment/box.png").convert_alpha(), (30, 30))
    
    # Icons and other
    images['heart_image'] = pygame.transform.scale(pygame.image.load("assets/menu_items/heart.png").convert_alpha(), (30, 30))
    images['pause_icon'] = pygame.transform.scale(pygame.image.load("assets/pauseicon.png").convert_alpha(), (30, 30))
    images['breakable_wall'] = pygame.transform.scale(pygame.image.load("assets/environment/wall.png").convert_alpha(), (30, 30))
    images['unbreakable_wall'] = pygame.transform.scale(pygame.image.load("assets/environment/brick.png").convert_alpha(), (30, 30))
    images['blue_cave'] = pygame.transform.scale(pygame.image.load("assets/environment/blue_cave.png").convert_alpha(), (30, 30))
    images['red_cave'] = pygame.transform.scale(pygame.image.load("assets/environment/red_cave.png").convert_alpha(), (30, 30))
    images['bomb_icon'] = pygame.transform.scale(pygame.image.load("assets/bomb.png").convert_alpha(), (30, 30))
    images['trap_image'] = pygame.transform.scale(pygame.image.load("assets/environment/manhole.png").convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
    
    return images