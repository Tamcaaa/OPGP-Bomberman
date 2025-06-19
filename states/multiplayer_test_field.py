

import pygame
import config
import copy
import time
import random

from states.state import State
from player import Player
from managers.music_manager import MusicManager
from power_up import PowerUp


class MultiplayerTestField(State):
    def __init__(self, game, selected_map, map_name):
        State.__init__(self, game)

        self.selected_map = selected_map
        self.map_name = map_name

        pygame.display.set_caption(f"BomberMan: {map_name}")
        self.game = game
        self.music_manager = MusicManager()

        self.keys_held = {pygame.K_s: False, pygame.K_d: False}

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()  # Group for power-ups

        # Hidden power-ups map - stores which bricks have power-ups underneath
        self.hidden_powerups = {}  # Format: {(x, y): powerup_type}

        self.player1 = Player(1, "spawn1", self)
        self.player2 = Player(2, "spawn4", self)
        self.players = [self.player1, self.player2]

        # Feedback message for power-ups
        self.powerup_message = ""
        self.message_timer = 0

        # Load images
        self.heart_image = pygame.image.load("assets/menu_items/heart.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))

        self.breakable_wall = pygame.image.load("assets/environment/wall.png").convert_alpha()
        self.breakable_wall = pygame.transform.scale(self.breakable_wall, (30, 30))

        self.unbreakable_wall = pygame.image.load("assets/environment/brick.png").convert_alpha()
        self.unbreakable_wall = pygame.transform.scale(self.unbreakable_wall, (30, 30))

        self.bomb_icon = pygame.image.load("assets/bomb.png").convert_alpha()
        self.bomb_icon = pygame.transform.scale(self.bomb_icon, (30, 30))

        self.tile_map = copy.deepcopy(selected_map)
        self.available_powerups = ["bomb_powerup", "range_powerup", "freeze_powerup", "live+_powerup", "shield_powerup"]
        self.load_music()
        self.place_hidden_powerups()
        self.trap_image = pygame.image.load("assets/environment/manhole.png").convert_alpha()
        self.trap_image = pygame.transform.scale(self.trap_image, (config.GRID_SIZE, config.GRID_SIZE))