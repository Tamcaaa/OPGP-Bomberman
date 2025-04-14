import pygame
import config
import os
import time
from bomb import Bomb
from states.test_field import *


class Player(pygame.sprite.Sprite):
    def __init__(self, game, player_num=1):
        super().__init__()
        self.game = game
        self.player_num = player_num  # 1 or 2
        self.photos_dir = os.path.join("photos", "player_color")

        # Load all directional sprites
        self.sprites = {
            "up": self.load_scaled_sprite(f"p_{player_num}_up.png"),
            "down": self.load_scaled_sprite(f"p_{player_num}_down.png"),
            "left": self.load_scaled_sprite(f"p_{player_num}_left.png"),
            "right": self.load_scaled_sprite(f"p_{player_num}_right.png")
        }

        # Set initial sprite and position
        self.direction = "down"
        self.image = self.sprites[self.direction]
        self.rect = self.image.get_rect()

        # Set initial position based on player number
        if player_num == 1:
            self.rect.topleft = (1 * config.GRID_SIZE, 1 * config.GRID_SIZE)
        else:
            self.rect.topleft = (25 * config.GRID_SIZE, 13 * config.GRID_SIZE)

        # Player properties
        self.speed = config.MOVE_SPEED  # Now in pixels per second
        self.lives = config.PLAYER_LIVES
        self.power = 2  # Bomb explosion range
        self.maxBombs = 3
        self.currentBomb = 0
        self.bomb_key_pressed = False
        self.invincible = False
        self.last_hit_time = 0
        self.invincibility_duration = 2
        self.blink = False
        self.blink_timer = 0
        self.blink_interval = 0.2
        self.is_dead = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.moving = {
            "up": False,
            "down": False,
            "left": False,
            "right": False
        }

    def load_scaled_sprite(self, filename):
        """Load and scale a sprite image."""
        image = pygame.image.load(os.path.join(self.photos_dir, filename)).convert_alpha()
        return pygame.transform.scale(image, (config.GRID_SIZE, config.GRID_SIZE))

    def update_movement(self, dt):
        """Update player position based on velocity and delta time."""
        # Reset velocity
        self.velocity.x = 0
        self.velocity.y = 0

        # Calculate velocity based on movement keys
        if self.moving["left"]:
            self.velocity.x = -1
            self.direction = "left"
            self.image = self.sprites["left"]
        if self.moving["right"]:
            self.velocity.x = 1
            self.direction = "right"
            self.image = self.sprites["right"]
        if self.moving["up"]:
            self.velocity.y = -1
            self.direction = "up"
            self.image = self.sprites["up"]
        if self.moving["down"]:
            self.velocity.y = 1
            self.direction = "down"
            self.image = self.sprites["down"]

        # Normalize diagonal movement
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * self.speed * dt

        # Update position
        new_x = self.rect.x + self.velocity.x
        new_y = self.rect.y + self.velocity.y

        # Boundary checking
        if 0 <= new_x <= config.SCREEN_WIDTH - config.GRID_SIZE:
            self.rect.x = new_x
        if 0 <= new_y <= config.SCREEN_HEIGHT - config.GRID_SIZE:
            self.rect.y = new_y

    def deployBomb(self, bomb_group, explosion_group):
        """Place a bomb at the player's current position if allowed."""
        if self.currentBomb < self.maxBombs:
            Bomb(self, bomb_group, explosion_group)
            self.currentBomb += 1
            return True
        return False

    def handle_bomb_placement(self, bomb_group, explosion_group, key_pressed):
        """
        Handle bomb placement with key press/release detection to prevent rapid firing.
        Returns True if bomb was placed.
        """
        if self.currentBomb >= self.maxBombs:
            return False

        if key_pressed:
            if not self.bomb_key_pressed:  # Only place bomb on initial press
                self.bomb_key_pressed = True
                return self.deployBomb(bomb_group, explosion_group)
        else:
            self.bomb_key_pressed = False
        return False

    def take_lives(self):
        """Reduce player's lives by 1 and handle game over if needed."""
        self.lives -= 1
        if self.lives < 0:  # Prevent lives from going below 0
            self.lives = 0

        if self.lives == 0:
            self.is_dead = True
            self.currentBomb = 0  # Reset bomb counter upon death
            self.game.all_sprites.remove(self)  # Remove from all sprite groups
            self.image = pygame.Surface((config.GRID_SIZE, config.GRID_SIZE))  # Make the player invisible
            self.image.set_alpha(0)  # Make the player transparent
            self.rect = self.image.get_rect()  # Update rect to match invisible image

            if self.player_num == 1:
                self.game.player1 = None  # Player 1 is removed
            else:
                self.game.player2 = None  # Player 2 is removed

            # Check if both players are dead
            if self.game.player1 is None and self.game.player2 is None:
                from states.game_over import GameOver
                new_state = GameOver(self.game)
                new_state.enter_state()

    def update(self):
        # Reset invincibility after cooldown
        now = time.time()
        if self.invincible and now - self.last_hit_time > self.invincibility_duration:
            self.invincible = False
            self.blink = False

    def hit_by_explosion(self):
        now = time.time()

        # Only react if the player isn't currently invincible
        if not self.invincible:
            self.invincible = True  # Make the player invincible temporarily
            self.last_hit_time = now
            self.blink = True  # Start blinking effect

            self.take_lives()