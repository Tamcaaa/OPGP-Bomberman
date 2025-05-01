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
        self.currentBomb = 1
        self.maxBombs = 1
        self.power = 1
        self.queued_keys = []
        self.last_move_time = 0
        self.iframe_timer = 0
        self.exited = False
        
        # Add key possession attribute
        self.has_key = False

        self.test_field = test_field
        self.music_manager = MusicManager()
        self.bomb_group = self.test_field.bomb_group
        self.explosion_group = self.test_field.explosion_group

        self.player_config = config.PLAYER_CONFIG[self.player_id]
        self.move_keys = self.player_config["move_keys"]

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
        now = time.time()
        if not now - self.iframe_timer >= config.PLAYER_IFRAMES:
            return
        if bool(pygame.sprite.spritecollide(self, self.explosion_group, False)):  # type: ignore[arg-type]
            self.iframe_timer = time.time()
            self.health -= 1
            return True
        return False

    def check_collect_item(self):
        grid_x = self.rect.x // config.GRID_SIZE
        grid_y = self.rect.y // config.GRID_SIZE

        if 0 <= grid_y < len(self.test_field.tile_map) and 0 <= grid_x < len(self.test_field.tile_map[0]):
            tile = self.test_field.tile_map[grid_y][grid_x]

            if tile == 7:  # Key
                self.has_key = True  # Key collected by any player
                self.test_field.tile_map[grid_y][grid_x] = 0  # Remove key tile from map
                self.test_field.has_key = True  # Update the global has_key flag in TestField
                print(f"Player {self.player_id} collected the key.")

            elif tile == 6 and self.test_field.has_key:  # Door and key has been collected
                if self.player_id not in self.test_field.players_exited:
                    self.test_field.players_exited.append(self.player_id)
                    print(f"Player {self.player_id} entered the door.")

                    # Move player offscreen (or deactivate)
                    self.rect.topleft = (-100, -100)

                    # Check if both players have exited
                    if len(self.test_field.players_exited) == len(self.test_field.players):
                        # If all players have exited, we can remove the door
                        self.test_field.tile_map[grid_y][grid_x] = 0  # Remove the door tile

                # Check if all players have exited and show victory
                if len(self.test_field.players_exited) == len(self.test_field.players):
                    pygame.mixer_music.stop()
                    self.test_field.exit_state()
                    self.test_field.game.state_manager.change_state("Victory")

        return False


    def get_player_location(self):
        return self.rect.x, self.rect.y

    def get_health(self):
        return self.health

    def handle_queued_keys(self, now):
        if self.queued_keys and now - self.last_move_time >= config.MOVE_COOLDOWN:
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
            
            # Check for item collection after movement
            self.check_collect_item()

    def move(self, dx, dy, direction):
        new_x = self.rect.x + dx * config.GRID_SIZE
        new_y = self.rect.y + dy * config.GRID_SIZE

        bound_x = max(0, min(new_x, config.SCREEN_WIDTH - config.GRID_SIZE))
        bound_y = max(0, min(new_y, config.SCREEN_HEIGHT - config.GRID_SIZE))

        # Check for collision with walls and bricks, but not with doors or keys
        tile_type = self.test_field.tile_map[bound_y // config.GRID_SIZE][bound_x // config.GRID_SIZE]

        # Prevent walking into walls, bricks, and unrevealed doors/keys (4, 5)
        if tile_type in [1, 2, 4, 5]:  # Wall, brick, hidden door/key
            self.image = self.images[direction]
            return

        self.music_manager.play_sound("walk", "walk_volume")
        # Boundary correction
        self.rect.x = bound_x
        self.rect.y = bound_y

        self.image = self.images[direction]  # Update sprite direction

    def deploy_bomb(self, bomb_group, explosion_group):
        if self.currentBomb > 0:
            Bomb(self, bomb_group, explosion_group, self.test_field)
            self.currentBomb -= 1  # Create bomb instance