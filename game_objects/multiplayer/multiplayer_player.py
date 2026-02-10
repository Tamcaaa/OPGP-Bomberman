import pygame
import config
import time
from game_objects.general.bomb import Bomb
from managers.music_manager import MusicManager
from typing import Tuple, Union, List

ColorLike = Union[pygame.Color, Tuple[int, int, int], Tuple[int, int, int, int]]



class Player(pygame.sprite.Sprite):
    def __init__(self, starting_location: str | tuple, test_field, name: str, player_color: Tuple[int, int, int], player_hat: str):
        super().__init__()
        self.name = name 
        self.player_color = player_color
        self.test_field = test_field
        self.music_manager = MusicManager()
        self.bomb_group = self.test_field.bomb_group
        self.explosion_group = self.test_field.explosion_group

        # ==================== Gameplay ====================
        self.health = config.HEALTH
        self.max_bomb_limit = config.MAX_BOMB_LIMIT
        self.currentBomb = config.CURRENTBOMB
        self.maxBombs = config.MAXBOMBS
        self.power = config.POWER  # Explosion range
        self.held_down_keys: List[int] = []
        self.last_move_time = config.LAST_MOVE_TIME
        self.score = config.SCORE
        self.last_trap_time = config.LAST_TRAP_TIME

        # ==================== Power-ups ====================
        self.active_powerups: dict[str, float] = {}
        self.freeze_timer = config.FREEZE_TIMER
        self.iframe_timer = config.IFRAME_TIMER

        # ==================== Animations ====================
        self.move_keys = config.DEFAULT_PLAYER1_MOVE_KEYS
        self.current_direction = "idle"
        self.moving = False
        self.frame_index = config.FRAME_INDEX
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = config.ANIM_FPS
        self.frame_duration = 1000 // self.anim_fps
        self.last_move_anim_time = 0  

        # ==================== Idle System ====================
        self.idle_start = pygame.time.get_ticks()
        self.afk_delay = config.AFK_DELAY

        # Load and scale images from config
        self.images: dict[str, list[pygame.Surface]] = {}
        for key, frames in config.PLAYER1_IMAGES.items():
            if isinstance(frames, list):
                self.images[key] = [
                    pygame.transform.scale(f.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                    for f in frames
                ]
            else:
                self.images[key] = [
                    pygame.transform.scale(frames.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                ]

        # Initialize image and position
        self.image = self.images["down"][0]
        self.rect = self.image.get_rect()
        if isinstance(starting_location, str):
            self.rect.topleft = config.SPAWN_POINTS[starting_location]
        else:
            self.rect.topleft = starting_location

        # Skin & Hat 
        self._player_hat: str = player_hat
        self.current_animation = "idle"
        self.current_frame_index = 0

        # Apply skin if provided
        self._apply_skin()

    # ==================== Skin & Hat ===================
    def _apply_skin(self):
        color = self.player_color
        for key, frames in config.PLAYER1_IMAGES.items():
            tinted_frames = []
            for frame in frames:
                base = pygame.transform.scale(frame.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                tinted = base.copy()
                tinted.fill(color, special_flags=pygame.BLEND_MULT)
                tinted_frames.append(tinted)
            self.images[key] = tinted_frames

        self.image = self.images[self.current_direction][self.frame_index]

    def has_hat(self) -> bool:
        if self._player_hat == 'None':
            return False
        return True
    
    def get_player_hat(self) -> str:
        return self._player_hat
    
    def set_player_hat(self,player_hat: str) -> None:
        if not player_hat in config.AVAILABLE_HATS.keys():
            raise Exception(f'[ERROR] player_hat: {player_hat} not in config.AVAILABLE_HATS: {config.AVAILABLE_HATS.keys()}')
        self._player_hat = player_hat

    # ==================== Gameplay Logic ====================
    def check_hit(self):
        now = pygame.time.get_ticks()
        if not now - self.iframe_timer >= config.PLAYER_IFRAMES:
            return

        if bool(pygame.sprite.spritecollide(self, self.explosion_group, False)):  # type: ignore[arg-type]
            self.iframe_timer = now
            self.music_manager.play_sound("hit", "level_volume")
            self.health -= 1
            return True
        return False

    def activate_powerup(self, powerup_type, duration=10):
        now = time.time()

        if powerup_type == "range_powerup":
            self.power += 1
        elif powerup_type == "bomb_powerup":
            self.maxBombs += 1
            self.currentBomb += 1
        elif powerup_type == "freeze_powerup":
            for player in self.test_field.players.values():
                if player.name != self.name:
                    player.freeze_timer = pygame.time.get_ticks() + (duration * 1000)
        elif powerup_type == "live+_powerup":
            self.health = min(self.health + 1, config.PLAYER_MAX_HEALTH)
        elif powerup_type == "shield_powerup":
            self.iframe_timer = pygame.time.get_ticks() + (duration * 1000)

        self.active_powerups[powerup_type] = now + duration

    def update_powerups(self):
        now = time.time()
        expired = [powerup for powerup, expire_time in self.active_powerups.items() if now >= expire_time]
        for powerup in expired:
            del self.active_powerups[powerup]

    def get_player_location(self):
        return self.rect.x, self.rect.y

    def get_health(self) -> int:
        return self.health

    def get_max_bombs(self) -> int:
        return self.maxBombs

    def handle_queued_keys(self, now):
        now = pygame.time.get_ticks()
        move_keys = self.move_keys

        move_delay = config.MOVE_COOLDOWN * 2 if now < self.freeze_timer else config.MOVE_COOLDOWN

        if now - self.last_move_time >= move_delay and self.held_down_keys:
            key = self.held_down_keys[-1]
            if key == move_keys[0]:
                self.move(0, -1, "up", send_packet=True)
            elif key == move_keys[2]:
                self.move(0, 1, "down", send_packet=True)
            elif key == move_keys[1]:
                self.move(-1, 0, "left", send_packet=True)
            elif key == move_keys[3]:
                self.move(1, 0, "right", send_packet=True)
            elif key == move_keys[4]:
                self.deploy_bomb(self.bomb_group, self.explosion_group)

            self.last_move_time = now

    def move(self, dx, dy, direction, send_packet: bool = False):
        new_x = self.rect.x + dx * config.GRID_SIZE
        new_y = self.rect.y + dy * config.GRID_SIZE

        bound_x = max(0, min(new_x, config.SCREEN_WIDTH - config.GRID_SIZE))
        bound_y = max(0, min(new_y, config.SCREEN_HEIGHT - config.GRID_SIZE))

        # Check collision with map
        tile_type = self.test_field.tile_map[bound_y // config.GRID_SIZE][bound_x // config.GRID_SIZE]
        if tile_type in [1, 2, 3]:
            self.moving = False
            self.current_direction = direction
            return

        # Check for teleport tiles
        if tile_type in [4, 5]:
            paired = self.find_paired_teleport(tile_type, bound_x, bound_y)
            if paired:
                bound_x, bound_y = paired

        # Check collision with bombs
        future_rect = self.rect.copy()
        future_rect.topleft = (bound_x, bound_y)
        for bomb in self.bomb_group:
            if not bomb.passable and bomb.rect.colliderect(future_rect):
                self.moving = False
                self.current_direction = direction
                return

        # Move and sync position
        self.rect.topleft = (bound_x, bound_y)
        self.moving = True
        self.current_direction = direction
        self.idle_start = pygame.time.get_ticks()
        num_frames = len(self.images.get(direction, self.images["idle"]))
        self.last_move_anim_time = pygame.time.get_ticks() + (num_frames * (1000 // self.anim_fps))
        self.music_manager.play_sound("walk", "walk_volume")

        if send_packet:
            packet_data = {
                "player_name": self.name,
                "direction": self.current_direction
            }
            self.test_field.send_packet('PLAYER_UPDATE', packet_data)

    def deploy_bomb(self, bomb_group, explosion_group):
        if self.currentBomb > 0:
            self.currentBomb -= 1
            Bomb(self, bomb_group, explosion_group, self.test_field)
            packet_data = {'player_name': self.name}
            self.test_field.send_packet('BOMB_UPDATE', packet_data)

    def find_paired_teleport(self, teleport_type, current_x, current_y):
        tiles = []
        for y, row in enumerate(self.test_field.tile_map):
            for x, tile in enumerate(row):
                if tile == teleport_type:
                    tile_x = x * config.GRID_SIZE
                    tile_y = y * config.GRID_SIZE
                    if tile_x == current_x and tile_y == current_y:
                        continue
                    tiles.append((tile_x, tile_y))
        return tiles[0] if tiles else None

    def update_animation(self):
        now = pygame.time.get_ticks()
        anim_key = self.current_direction if self.moving else "idle"

        if anim_key not in self.images:
            anim_key = "idle"

        frames = self.images[anim_key]
        frame_duration = 1000 / self.anim_fps if self.moving else 500

        if now - self.last_anim_update >= frame_duration:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.last_anim_update = now

        self.image = frames[self.frame_index]
        self.current_animation = anim_key
        self.current_frame_index = self.frame_index
