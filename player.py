import pygame
import config
import os
import time
from bomb import Bomb

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
        self.speed = config.MOVE_SPEED
        self.lives = config.PLAYER_LIVES
        self.power = config.POWER  # Bomb explosion range
        self.maxBombs = config.MAXBOMBS
        self.currentBomb = config.CURRENTBOMBS
        self.bomb_key_pressed = False
        self.invincible = False
        self.last_hit_time = config.LAST_HIT_TIME
        self.last_move_time = config.LAST_MOVE_TIME
        self.invincibility_duration = config.INVICIBILITY_DURATION
        self.blink = False
        self.blink_timer = config.BLINK_TIMER
        self.blink_interval = config.BLINK_INTERVAL
        self.is_dead = False

    def load_scaled_sprite(self, filename):
        """Load and scale a sprite image."""
        image = pygame.image.load(os.path.join(self.photos_dir, filename)).convert_alpha()
        return pygame.transform.scale(image, (config.GRID_SIZE, config.GRID_SIZE))

    def move(self, dx, dy, direction):
        """Move the player in the specified direction with proper collision detection."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < 1000 / self.speed:
            return

        # Update direction and sprite
        if direction != self.direction:
            self.direction = direction
            self.image = self.sprites[self.direction]

        # Store original position
        original_x = self.rect.x
        original_y = self.rect.y

        # Calculate new position
        new_x = original_x + dx * config.GRID_SIZE
        new_y = original_y + dy * config.GRID_SIZE

        # Check for wall collisions individually in each direction
        # First check horizontal movement
        temp_rect = self.rect.copy()
        temp_rect.x = new_x
        temp_rect.y = original_y
        
        if self.can_move_to_position(temp_rect):
            self.rect.x = new_x
        
        # Then check vertical movement
        temp_rect = self.rect.copy()
        temp_rect.x = self.rect.x  # Use possibly updated x position
        temp_rect.y = new_y
        
        if self.can_move_to_position(temp_rect):
            self.rect.y = new_y
        
        # Only play sound if player actually moved
        if self.rect.x != original_x or self.rect.y != original_y:
            self.last_move_time = current_time
            walk_sound = pygame.mixer.Sound("sounds/walk.wav")
            walk_sound.play()
    
    def can_move_to_position(self, rect):
        """Check if player can move to the given position."""
        # Get the level from the current state stack
        current_state = self.game.state_stack[-1]
        level = current_state.level
        
        # Calculate grid coordinates for all corners of the player's rect
        # We'll check if any corner is in a non-empty tile
        grid_positions = [
            (rect.left // config.GRID_SIZE, rect.top // config.GRID_SIZE),    # Top-left
            ((rect.right - 1) // config.GRID_SIZE, rect.top // config.GRID_SIZE),   # Top-right
            (rect.left // config.GRID_SIZE, (rect.bottom - 1) // config.GRID_SIZE), # Bottom-left
            ((rect.right - 1) // config.GRID_SIZE, (rect.bottom - 1) // config.GRID_SIZE) # Bottom-right
        ]
        
        # Check if any corner is in a wall or brick
        for grid_x, grid_y in grid_positions:
            # Check boundaries
            if grid_x < 0 or grid_x >= level.width or grid_y < 0 or grid_y >= level.height:
                return False
            
            # Check if tile is a wall or brick
            if level.grid[grid_y][grid_x] != 0:  # Not empty
                return False
        
        # Check for bomb collisions - bomb_group is in the current state
        if hasattr(current_state, 'bomb_group'):
            for bomb in current_state.bomb_group:
                if rect.colliderect(bomb.rect):
                    # Don't collide with the player's own bombs immediately after placing them
                    # This prevents the player from getting stuck on their own bombs
                    if bomb.owner == self and bomb.just_placed:
                        continue
                    return False
                
        return True

    def deployBomb(self, bomb_group, explosion_group):
        """Place a bomb at the player's current position if allowed."""
        if self.currentBomb < self.maxBombs:
            # Calculate grid position for bomb placement
            grid_x = (self.rect.x + config.GRID_SIZE // 2) // config.GRID_SIZE
            grid_y = (self.rect.y + config.GRID_SIZE // 2) // config.GRID_SIZE
            
            # Create bomb at center of tile
            bomb_x = grid_x * config.GRID_SIZE
            bomb_y = grid_y * config.GRID_SIZE
            
            # Check if there's already a bomb at this position
            for bomb in bomb_group:
                if bomb.rect.x == bomb_x and bomb.rect.y == bomb_y:
                    return False
            
            Bomb(self, bomb_group, explosion_group, position=(bomb_x, bomb_y))
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
            pygame.mixer.Sound("sounds/die.wav").play()
            
            if self.player_num == 1:
                self.game.player1 = None  # Player 1 is removed
            else:
                self.game.player2 = None  # Player 2 is removed

            # Check if both players are dead
            if self.game.player1 is None and self.game.player2 is None:
                from states.game_over import GameOver
                new_state = GameOver(self.game)
                new_state.enter_state()
                pygame.mixer.Sound("sounds/game_over.wav").play()

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