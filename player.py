import pygame
import config
import time
from bomb import Bomb
from maps.test_field_map import tile_map


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

        self.bomb_group = test_field.bomb_group
        self.explosion_group = test_field.explosion_group

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

    def move(self, dx, dy, direction):
        if tile_map[max(0, min((self.rect.y + dy * config.GRID_SIZE), config.SCREEN_HEIGHT - config.GRID_SIZE)) // 30][
            max(0, min((self.rect.x + dx * config.GRID_SIZE), config.SCREEN_WIDTH - config.GRID_SIZE)) // 30] == 1:
            self.image = self.images[direction]
            return

        """Move the player and update sprite based on direction."""
        self.rect.x += dx * config.GRID_SIZE
        self.rect.y += dy * config.GRID_SIZE

        # Boundary correction
        self.rect.x = max(0, min(self.rect.x, config.SCREEN_WIDTH - config.GRID_SIZE))
        self.rect.y = max(0, min(self.rect.y, config.SCREEN_HEIGHT - config.GRID_SIZE))

        self.image = self.images[direction]  # Update sprite direction

    def deploy_bomb(self, bomb_group, explosion_group):
        if self.currentBomb > 0:
            Bomb(self, bomb_group, explosion_group)  # Používame správnu triedu!
            self.currentBomb -= 1  # Create bomb instance
