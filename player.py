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
        self.speed = 1  # Movement speed multiplier
        self.queued_keys = []
        self.last_move_time = 0
        self.iframe_timer = 0
        self.score = 0
        

        self.test_field = test_field
        self.music_manager = MusicManager()
        self.bomb_group = self.test_field.bomb_group
        self.explosion_group = self.test_field.explosion_group

        self.player_config = config.PLAYER_CONFIG[self.player_id]
        self.move_keys = self.player_config["move_keys"]
        
        # Power-up effects
        self.active_powerups = {}  # Track active power-ups and their timers
        self.freeze_timer = 0
        self.invincible_timer = 0

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
            return False
            
        # Temporary invincibility from power-up check
        if self.invincible_timer > 0 and now < self.invincible_timer:
            return False
            
        # Check collision with explosions
        if bool(pygame.sprite.spritecollide(self, self.explosion_group, False)):  # type: ignore[arg-type]
            self.iframe_timer = time.time()
            self.health -= 1
            return True
        return False
            
    def slow_other_player(self):
        """Apply freeze effect to the other player"""
        other_player = self.test_field.player2 if self.player_id == 1 else self.test_field.player1
        other_player.freeze_timer = time.time() + 5  # Apply freeze effect for 5 seconds
            
    def activate_powerup(self, powerup_type, duration=30):
        """Activate a power-up effect"""
        now = time.time()
        
        if powerup_type == "speed_powerup":
            # Increase explosion range
            self.power += 1
            
        elif powerup_type == "bomb_powerup":
            # Increase max bombs
            self.maxBombs += 1
            self.currentBomb += 1
            
        elif powerup_type == "freeze_powerup":
            # Freeze other player
            self.slow_other_player()
            
        elif powerup_type == "live+_powerup":
            # Add extra life (up to maximum of 5)
            self.health = min(self.health + 1, 5)
            
        elif powerup_type == "shield_powerup":
            # Temporary invincibility
            self.invincible_timer = now + duration
            
        # Add power-up to active list with expiration time for temporary effects
        self.active_powerups[powerup_type] = now + duration
    
    def update_powerups(self):
        """Update active power-ups and remove expired ones"""
        now = time.time()
        expired = []
        
        for powerup, expire_time in self.active_powerups.items():
            if now >= expire_time:
                expired.append(powerup)
                
                # Handle removing temporary effects
                if powerup == "bomb_powerup":
                    self.maxBombs = max(1, self.maxBombs - 1)  # Return to normal, minimum 1
                    
                elif powerup == "speed_powerup":
                    self.power = max(1, self.power - 1)  # Return to normal, minimum 1
                    
        # Remove expired power-ups
        for powerup in expired:
            del self.active_powerups[powerup]
        
    def get_player_location(self):
        """Get player's current position"""
        return self.rect.x, self.rect.y

    def get_health(self):
        """Get player's current health"""
        return self.health

    def handle_queued_keys(self, now):
        """Process queued movement keys"""
        self.update_powerups()  # Always keep power-ups updated

        # Block movement while frozen
        if time.time() < self.freeze_timer:
            move_delay = config.MOVE_COOLDOWN * 2.0  # slower
        else:
            move_delay = config.MOVE_COOLDOWN / self.speed

        move_delay = config.MOVE_COOLDOWN / self.speed

        if self.queued_keys and now - self.last_move_time >= move_delay:
            key = self.queued_keys.pop(0)
            if key == pygame.K_w or key == pygame.K_UP:
                self.move(0, -1, "up")
            elif key == pygame.K_s or key == pygame.K_DOWN:
                self.move(0, 1, "down")
            elif key == pygame.K_a or key == pygame.K_LEFT:
                self.move(-1, 0, "left")
            elif key == pygame.K_d or key == pygame.K_RIGHT:
                self.move(1, 0, "right")
            elif key == pygame.K_SPACE or key == pygame.K_KP0:
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
        if tile_type in [1, 2]:  # Wall, brick
            self.image = self.images[direction]
            return

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