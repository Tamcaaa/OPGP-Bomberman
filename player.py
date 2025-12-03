import pygame
import config
import os
import time
from bomb import Bomb
from managers.music_manager import MusicManager
from typing import Optional, Tuple, Union, List

ColorLike = Union[pygame.Color, Tuple[int, int, int], Tuple[int, int, int, int]]
SkinPayload = Union[None, ColorLike, Tuple[ColorLike, str]]


class Player(pygame.sprite.Sprite):
    def __init__(self, player_id: int, starting_location: str | tuple, test_field, skin: SkinPayload = None):
        super().__init__()

        self.player_id = player_id
        self.skin = skin
        self.test_field = test_field
        self.music_manager = MusicManager()
        self.bomb_group = self.test_field.bomb_group
        self.explosion_group = self.test_field.explosion_group

        # ---------------- Gameplay Vars ----------------
        self.health = config.HEALTH
        self.max_bomb_limit = config.MAX_BOMB_LIMIT
        self.currentBomb = config.CURRENTBOMB
        self.maxBombs = config.MAXBOMBS
        self.power = config.POWER            # Explosion range
        self.queued_keys: List[int] = []
        self.held_down_keys: List[int] = []
        self.last_move_time = config.LAST_MOVE_TIME
        self.score = config.SCORE
        self.last_trap_time = config.LAST_TRAP_TIME

        # ---------------- PowerUps ----------------
        self.active_powerups: dict[str, float] = {}
        self.freeze_timer = config.FREEZE_TIMER
        self.iframe_timer = config.IFRAME_TIMER

        # ---------------- Animations ----------------
        self.player_config = config.PLAYER_CONFIG[self.player_id]
        self.move_keys = self.player_config["move_keys"]
        self.current_direction = "idle"
        self.moving = False
        self.frame_index = config.FRAME_INDEX
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = config.ANIM_FPS
        self.frame_duration = 1000 // self.anim_fps

        # ---------------- Idle Systems ----------------
        self.idle_start = pygame.time.get_ticks()
        self.afk_delay = config.AFK_DELAY

        # Načítanie obrázkov z configu do self.images
        self.images: dict[str, list[pygame.Surface]] = {}
        for key, frames in self.player_config["images"].items():
            if isinstance(frames, list):
                self.images[key] = [
                    pygame.transform.scale(f.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                    for f in frames
                ]
            else:
                self.images[key] = [
                    pygame.transform.scale(frames.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                ]

        # Východzia snímka a pozícia
        self.image = self.images["down"][0]
        self.rect = self.image.get_rect()
        if isinstance(starting_location, str):
            self.rect.topleft = config.SPAWN_POINTS[starting_location]
        else:
            self.rect.topleft = starting_location

        # --- Skin & Hat podpora ---
        self.hat: Optional[str] = None
        self.skin: Optional[Tuple[int, int, int] | Tuple[int, int, int, int]] = self._normalize_skin(skin)

        # Aplikuj skin (ak je)
        self.apply_skin()

    # =======================
    # Pomocné / Skin & Hat
    # =======================
    def _normalize_skin(self, skin: SkinPayload):
        """
        Vráti čisté RGB(A) pre farbenie. Ak príde ((r,g,b[,(a)]), "HatName"),
        uloží hat do self.hat a vráti len farbu. Ak formát nesedí -> None.
        """
        if skin is None:
            return None

        # (color_like, "HatName")
        if isinstance(skin, (tuple, list)) and len(skin) == 2:
            color_part, maybe_hat = skin
            # ulož hat (aj keby neskôr nebol použitý)
            try:
                self.hat = str(maybe_hat) if maybe_hat is not None else None
            except Exception:
                self.hat = None
            skin = color_part  # ďalej budeme riešiť už len farbu

        # pygame.Color -> RGBA tuple
        if isinstance(skin, pygame.Color):
            return (skin.r, skin.g, skin.b, skin.a)

        # (r,g,b) alebo (r,g,b,a)
        if isinstance(skin, (tuple, list)) and len(skin) in (3, 4):
            # validácia zložiek
            try:
                comps = tuple(int(c) for c in skin)
                if len(comps) == 3:
                    r, g, b = comps
                    return (max(0, min(255, r)),
                            max(0, min(255, g)),
                            max(0, min(255, b)))
                else:
                    r, g, b, a = comps
                    return (max(0, min(255, r)),
                            max(0, min(255, g)),
                            max(0, min(255, b)),
                            max(0, min(255, a)))
            except Exception:
                return None

        # nič z vyššie uvedeného – ignoruj
        return None

    def apply_skin(self):
        """Aplikuje farebný skin na všetky snímky hráča (bezpečne)."""
        if not self.skin:
            return  # žiadny skin -> nič nefarbíme

        # zabezpeč, že máme RGB(A)
        color = self.skin
        # Pygame BLEND_MULT funguje s RGB(A) – ak príde len RGB, je OK
        for key, frames in self.player_config["images"].items():
            tinted_frames = []
            iterable = frames if isinstance(frames, list) else [frames]
            for frame in iterable:
                base = pygame.transform.scale(frame.convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE))
                tinted = base.copy()
                # fill vyžaduje validnú farbu -> tu už je validované
                tinted.fill(color, special_flags=pygame.BLEND_MULT)
                tinted_frames.append(tinted)
            self.images[key] = tinted_frames

        # aktívny frame nech ostane konzistentný s aktuálnym smerom
        self.image = self.images[self.current_direction][self.frame_index]

    # =======================
    # Gameplay logika
    # =======================
    def check_hit(self):
        """Check if player is hit by an explosion (s i-frame ochrannou)."""
        now = time.time()

        # Invincibility frames check
        if not now - self.iframe_timer >= config.PLAYER_IFRAMES:
            return
        if bool(pygame.sprite.spritecollide(self, self.explosion_group, False)):  # type: ignore[arg-type]
            self.iframe_timer = time.time()
            self.music_manager.play_sound("hit", "level_volume")
            self.health -= 1
            return True
        return False

    def activate_powerup(self, powerup_type, duration=10):
        """Activate a power-up effect."""
        now = time.time()

        if powerup_type == "range_powerup":
            self.power += 1
        elif powerup_type == "bomb_powerup":
            self.maxBombs += 1
            self.currentBomb += 1
        elif powerup_type == "freeze_powerup":
            other_player = self.test_field.player2 if self.player_id == 1 else self.test_field.player1
            other_player.freeze_timer = time.time() + duration
        elif powerup_type == "live+_powerup":
            self.health = min(self.health + 1, config.PLAYER_MAX_HEALTH)
        elif powerup_type == "shield_powerup":
            self.iframe_timer = now + duration

        self.active_powerups[powerup_type] = now + duration

    def update_powerups(self):
        """Update active power-ups and remove expired ones."""
        now = time.time()
        expired = []
        for powerup, expire_time in self.active_powerups.items():
            if now >= expire_time:
                expired.append(powerup)
        for powerup in expired:
            del self.active_powerups[powerup]

    def get_player_location(self):
        return self.rect.x, self.rect.y

    def get_health(self) -> int:
        return self.health

    def get_max_bombs(self) -> int:
        return self.maxBombs

    def handle_queued_keys(self, now):
        """Spracuje „držané“ klávesy s cooldownom (zahŕňa freeze spomalenie)."""
        now = pygame.time.get_ticks()
        move_keys = self.move_keys

        move_delay = config.MOVE_COOLDOWN * 2 if now < self.freeze_timer else config.MOVE_COOLDOWN

        if now - self.last_move_time >= move_delay and self.held_down_keys:
            key = self.held_down_keys[-1]
            if key == move_keys[0]:      # Up
                self.move(0, -1, "up")
            elif key == move_keys[2]:    # Down
                self.move(0, 1, "down")
            elif key == move_keys[1]:    # Left
                self.move(-1, 0, "left")
            elif key == move_keys[3]:    # Right
                self.move(1, 0, "right")
            elif key == move_keys[4]:    # Bomb
                self.deploy_bomb(self.bomb_group, self.explosion_group)

            self.last_move_time = now

    def move(self, dx, dy, direction):
        """Move the player in the specified direction."""
        new_x = self.rect.x + dx * config.GRID_SIZE
        new_y = self.rect.y + dy * config.GRID_SIZE

        bound_x = max(0, min(new_x, config.SCREEN_WIDTH - config.GRID_SIZE))
        bound_y = max(0, min(new_y, config.SCREEN_HEIGHT - config.GRID_SIZE))

        # Kolízia s mapou
        tile_type = self.test_field.tile_map[bound_y // config.GRID_SIZE][bound_x // config.GRID_SIZE]
        if tile_type in [1, 2, 3]:
            self.moving = False
            self.current_direction = direction
            return

        # Teleport
        if tile_type in [4, 5]:
            paired = self.find_paired_teleport(tile_type, bound_x, bound_y)
            if paired:
                bound_x, bound_y = paired

        # Kolízia s bombami
        future_rect = self.rect.copy()
        future_rect.topleft = (bound_x, bound_y)
        for bomb in self.bomb_group:
            if not bomb.passable and bomb.rect.colliderect(future_rect):
                self.moving = False
                self.current_direction = direction
                return

        # Pohyb
        self.rect.topleft = (bound_x, bound_y)
        self.moving = True
        self.current_direction = direction
        self.idle_start = pygame.time.get_ticks()
        self.music_manager.play_sound("walk", "walk_volume")

    def deploy_bomb(self, bomb_group, explosion_group):
        """Deploy a bomb at the player's current position."""
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
                        continue  # preskoč aktuálny tile
                    tiles.append((tile_x, tile_y))
        if tiles:
            return tiles[0]  # jednoduché párovanie
        return None

    def update_animation(self):
        """Aktualizuje animácie hráča (idle + walk) s použitím skinned snímok."""

        now = pygame.time.get_ticks()
        anim_key = self.current_direction if self.moving else "idle"

        if anim_key not in self.images:  # bezpečnostný fallback
            anim_key = "idle"

        frames = self.images[anim_key]
        frame_duration = 1000 / self.anim_fps if self.moving else 500

        if now - self.last_anim_update >= frame_duration:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.last_anim_update = now

        self.image = frames[self.frame_index]
        self.current_animation = anim_key
        self.current_frame_index = self.frame_index

        
    def load_sprites(self):
        # Idle frame
        self.idle_frames = []
        for i in range(3):
            frame = pygame.image.load(
                os.path.join("assets/player_color", f"p_{self.player_id}_idle_{i}.png")
            ).convert_alpha()
            self.idle_frames.append(pygame.transform.scale(frame, (frame.get_width()*8, frame.get_height()*8)))

        # Farba z SkinSelector
        if self.skin and self.skin[0]:  # self.skin = (color, hat_name)
            self.idle_frames = [self.tint_image(f, self.skin[0]) for f in self.idle_frames]

        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect()

    def tint_image(self, image, color):
        tinted = image.copy()
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))
        tinted.blit(tint, (0,0), special_flags=pygame.BLEND_MULT)
        return tinted
    def update_movement_status(self):
        self.moving = False
        if self.held_down_keys:
            if pygame.K_w in self.held_down_keys or pygame.K_UP in self.held_down_keys:
                self.current_direction = "up"
                self.moving = True
            elif pygame.K_s in self.held_down_keys or pygame.K_DOWN in self.held_down_keys:
                self.current_direction = "down"
                self.moving = True
            elif pygame.K_a in self.held_down_keys or pygame.K_LEFT in self.held_down_keys:
                self.current_direction = "left"
                self.moving = True
            elif pygame.K_d in self.held_down_keys or pygame.K_RIGHT in self.held_down_keys:
                self.current_direction = "right"
                self.moving = True


