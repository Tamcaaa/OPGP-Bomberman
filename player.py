import pygame
import config
import time
from bomb import Bomb
from managers.music_manager import MusicManager


class Player(pygame.sprite.Sprite):
    def __init__(self, player_id: int, starting_location: str | tuple, test_field):
        super().__init__()

        self.player_id = player_id

        if self.player_id not in config.PLAYER_CONFIG:
            raise ValueError(f"Invalid player id {self.player_id}")

        self.health = 3
        self.max_bomb_limit = 4
        self.currentBomb = 1
        self.maxBombs = 1
        self.power = 1  # Explosion range
        self.queued_keys = []
        self.held_down_keys = []
        self.last_move_time = 0
        self.score = 0
        self.last_trap_time = 0
        self.test_field = test_field
        self.music_manager = MusicManager()
        self.bomb_group = self.test_field.bomb_group
        self.explosion_group = self.test_field.explosion_group

        self.player_config = config.PLAYER_CONFIG[self.player_id]
        self.move_keys = self.player_config["move_keys"]

        # Power-up effects
        self.active_powerups = {}  # Track active power-ups and their timers
        self.freeze_timer = 0
        self.iframe_timer = 0

        # Dict of all images of player
        self.images = {
            key: pygame.transform.scale(img.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
            for key, img in self.player_config["images"].items()
        }

        self.image = self.images["down"]  # Default direction image
        self.rect = self.image.get_rect()
        if isinstance(starting_location, str):
            self.rect.topleft = config.SPAWN_POINTS[starting_location]
        else:
            self.rect.topleft = starting_location
        self.move_timer = 0  # Timer for movement delay

    def check_hit(self):
        """Check if player is hit by an explosion"""
        now = time.time()

        # Invincibility frames check
        if not now - self.iframe_timer >= config.PLAYER_IFRAMES:
            return
        if bool(pygame.sprite.spritecollide(self, self.explosion_group, False)):  # type: ignore[arg-type]
            self.iframe_timer = time.time()
            self.health -= 1
            return True
        return False

    def activate_powerup(self, powerup_type, duration=10):
        """Activate a power-up effect"""
        now = time.time()

        if powerup_type == "range_powerup":
            # Increase explosion range
            self.power += 1
        elif powerup_type == "bomb_powerup":
            # Increase max bombs
            self.maxBombs += 1
            self.currentBomb += 1
        elif powerup_type == "freeze_powerup":
            # Freeze other player
            other_player = self.test_field.player2 if self.player_id == 1 else self.test_field.player1
            other_player.freeze_timer = time.time() + duration
        elif powerup_type == "live+_powerup":
            # Add extra life
            self.health = min(self.health + 1, config.PLAYER_MAX_HEALTH)

        elif powerup_type == "shield_powerup":
            # Temporary invincibility
            self.iframe_timer = now + duration

        # Add power-up to active list with expiration time for temporary effects
        self.active_powerups[powerup_type] = now + duration

    def update_powerups(self):
        """Update active power-ups and remove expired ones"""
        now = time.time()
        expired = []

        for powerup, expire_time in self.active_powerups.items():
            if now >= expire_time:
                expired.append(powerup)
                # Here add temporary powerups if needed
        # Remove expired power-ups
        for powerup in expired:
            del self.active_powerups[powerup]

    def get_player_location(self):
        """Get player's current position"""
        return self.rect.x, self.rect.y

    def get_health(self) -> int:
        """Get player's current health"""
        return self.health

    def get_max_bombs(self) -> int:
        return self.maxBombs

    def handle_queued_keys(self, now):
        # Získání kláves z konfigurace
        move_keys = self.player_config['move_keys']

        if time.time() < self.freeze_timer:
            move_delay = config.MOVE_COOLDOWN * 2.0  # slower
        else:
            move_delay = config.MOVE_COOLDOWN

        if now - self.last_move_time >= move_delay and self.held_down_keys:
            self.queued_keys.append(self.held_down_keys[-1])
            key = self.queued_keys.pop(0)
            if key == move_keys[0]:  # Up
                self.move(0, -1, "up")
            elif key == move_keys[2]:  # Down
                self.move(0, 1, "down")
            elif key == move_keys[1]:  # Left
                self.move(-1, 0, "left")
            elif key == move_keys[3]:  # Right
                self.move(1, 0, "right")
            elif key == move_keys[4]:  # Bomb
                self.deploy_bomb(self.bomb_group, self.explosion_group)
            self.last_move_time = now

    def move(self, dx, dy, direction):
        """Move the player in the specified direction"""
        new_x = self.rect.x + dx * config.GRID_SIZE
        new_y = self.rect.y + dy * config.GRID_SIZE

        bound_x = max(0, min(new_x, config.SCREEN_WIDTH - config.GRID_SIZE))
        bound_y = max(0, min(new_y, config.SCREEN_HEIGHT - config.GRID_SIZE))

        # Check for collision with walls and bricks
        tile_type = self.test_field.tile_map[bound_y // config.GRID_SIZE][bound_x // config.GRID_SIZE]

        # Prevent walking into walls and bricks
        if tile_type in [1, 2, 3]:  # Wall, brick, Menu
            self.image = self.images[direction]
            return
        
        # Teleport logic: if tile is a teleport tile, find paired teleport location
        if tile_type in [4, 5]:  # Assuming 4 = red cave, 5 = blue cave
            paired_pos = self.find_paired_teleport(tile_type, bound_x, bound_y)
            if paired_pos:
                bound_x, bound_y = paired_pos
                
         # Check for collision with bombs
        future_rect = self.rect.copy()
        future_rect.x = bound_x
        future_rect.y = bound_y
        for bomb in self.bomb_group:
            if not bomb.passable and bomb.rect.colliderect(future_rect):
                self.image = self.images[direction]
                return  # Block movement if colliding with any bomb
    

        self.music_manager.play_sound("walk", "walk_volume")
        # Boundary correction
        self.rect.x = bound_x
        self.rect.y = bound_y

        self.image = self.images[direction]  # Update sprite direction

    def deploy_bomb(self, bomb_group, explosion_group):
        """Deploy a bomb at the player's current position"""
        if self.currentBomb > 0:
            Bomb(self, bomb_group, explosion_group, self.test_field)
            self.currentBomb -= 1  # Decrement available bombs
    def find_paired_teleport(self, teleport_type, current_x, current_y):
        
        tiles = []
    
        for y, row in enumerate(self.test_field.tile_map):
            for x, tile in enumerate(row):
                if tile == teleport_type:
                    tile_x = x * config.GRID_SIZE
                    tile_y = y * config.GRID_SIZE
                    if tile_x == current_x and tile_y == current_y:
                        continue  # skip current tile
                    tiles.append((tile_x, tile_y))
    
        if tiles:
            # Return first other teleport found, assuming only one paired teleport
            return tiles[0]
        return None