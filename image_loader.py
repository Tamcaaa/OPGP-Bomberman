import os
import pygame
import config
from typing import List, Dict

def load_images():
    images = {}
    
    # Backgrounds
    images['cave_bg'] = pygame.image.load("assets/backgrounds/map/cave-bg.png").convert_alpha()
    images['grass_bg'] = pygame.image.load("assets/backgrounds/map/grass-bg.png").convert_alpha()
    images['ruins_bg'] = pygame.image.load("assets/backgrounds/map/ruins_bg.png").convert_alpha()
    images['sand_bg'] = pygame.image.load("assets/backgrounds/map/sand-bg.png").convert_alpha()
    images['urban_bg'] = pygame.image.load("assets/backgrounds/map/urban_bg.png").convert_alpha()

    # Menu backgrounds
    images['menu_bg'] = pygame.image.load("assets/backgrounds/menu/bg.png").convert_alpha()
    images['pause_bg'] = pygame.image.load("assets/backgrounds/menu/pause.png").convert_alpha()
    images['skinselector_bg'] = pygame.image.load("assets/backgrounds/menu/skinselector_bg.png").convert_alpha()
    images['battlefield_bg'] = pygame.image.load("assets/backgrounds/menu/battlefield-bg.png").convert_alpha()

    # Titles
    images['title'] = pygame.image.load("assets/backgrounds/titles/bomber-man-text.png").convert_alpha()
    # Unbreakable and breakable tiles
    images['unbreakable_stone'] = pygame.transform.scale(pygame.image.load("assets/environment/stone-black.png").convert_alpha(), (30, 30))
    images['breakable_barrel'] = pygame.transform.scale(pygame.image.load("assets/environment/barrel.png").convert_alpha(), (30, 30))
    images['breakable_bush'] = pygame.transform.scale(pygame.image.load("assets/environment/bush.png").convert_alpha(), (30, 30))
    images['unbreakable_rock'] = pygame.transform.scale(pygame.image.load("assets/environment/black-block-rock.png").convert_alpha(), (30, 30))
    images['breakable_rock'] = pygame.transform.scale(pygame.image.load("assets/environment/rock.png").convert_alpha(), (30, 30))
    images['breakable_diamond'] = pygame.transform.scale(pygame.image.load("assets/environment/diamond.png").convert_alpha(), (30, 30))
    images['breakable_cactus'] = pygame.transform.scale(pygame.image.load("assets/environment/cactus.png").convert_alpha(), (30, 30))
    images['unbreakable_box'] = pygame.transform.scale(pygame.image.load("assets/environment/box.png").convert_alpha(), (30, 30))
    images['breakable_wall'] = pygame.transform.scale(pygame.image.load("assets/environment/wall.png").convert_alpha(), (30, 30))
    images['unbreakable_wall'] = pygame.transform.scale(pygame.image.load("assets/environment/brick.png").convert_alpha(), (30, 30))
    images['blue_cave'] = pygame.transform.scale(pygame.image.load("assets/environment/blue_cave.png").convert_alpha(), (30, 30))
    images['red_cave'] = pygame.transform.scale(pygame.image.load("assets/environment/red_cave.png").convert_alpha(), (30, 30))
    images['trap_image'] = pygame.transform.scale(pygame.image.load("assets/environment/manhole.png").convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
    
    # Player animations
    images['player_idle'] = [
    pygame.image.load(f"assets/player_animations/p_1_idle_{i}.png").convert_alpha()
    for i in range(3)]

    # Icons and other
    images['heart_image'] = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
    images['heart_image'] = pygame.transform.scale(images['heart_image'], (30, 30))
    images["bomb_icon"] = pygame.image.load("assets/player_items/bomb.png").convert_alpha()
    images["bomb_icon"] = pygame.transform.scale(images["bomb_icon"], (30, 30))
    return images

def load_hat_images():
    hat_images = {}
    hat_thumbs = {}

    for hat in config.HATS:
        name = hat["name"]
        file = hat["file"]

        if file is None:
            hat_images[name] = None
            hat_thumbs[name] = None
            continue

        path = os.path.join("assets/player_hats", file)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (48, 48))

        hat_images[name] = img

        scale = config.TW / max(img.get_width(), img.get_height())
        thumb = pygame.transform.smoothscale(
            img,
            (int(img.get_width() * scale), int(img.get_height() * scale))
        )
        hat_thumbs[name] = thumb

    return hat_images, hat_thumbs