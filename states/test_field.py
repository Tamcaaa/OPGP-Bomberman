import pygame
import config
import copy
import time
import random
import os

from states.state import State
from player import Player
from managers.music_manager import MusicManager
from power_up import PowerUp
from states.skin_selector import HATS


class TestField(State):
    def __init__(self, game, selected_map, map_name, selected_skins=None):
        State.__init__(self, game)

        self.selected_map = selected_map
        self.map_name = map_name
        self.selected_skins = selected_skins or {}

        pygame.display.set_caption(f"BomberMan: {map_name}")
        self.game = game
        self.music_manager = MusicManager()

        self.keys_held = {pygame.K_s: False, pygame.K_d: False}

        self.bomb_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()
        self.hidden_powerups = {}  # {(x, y): powerup_type}

        self.player1 = Player(1, "spawn1", self, skin=self.selected_skins.get(1))
        self.player2 = Player(2, "spawn4", self, skin=self.selected_skins.get(2))
        self.players = [self.player1, self.player2]

        self.powerup_message = ""
        self.message_timer = 0

        # --- Load hat images directly in TestField ---
        self.hat_images = {}

        for hat_def in HATS:
            name = hat_def["name"]
            if name != "None":
                file_name = f"{name.lower()}.png"  # alebo použij presný názov súboru
                path = os.path.join(game.photos_dir, "../assets/player_hats", file_name)
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (config.GRID_SIZE, config.GRID_SIZE))
                self.hat_images[name] = img

        # --- Load backgrounds ---
        self.cave_bg = pygame.image.load("assets/cave-bg.png").convert_alpha()
        self.grass_bg = pygame.image.load("assets/grass-bg.png").convert_alpha()
        self.sand_bg = pygame.image.load("assets/sand-bg.png").convert_alpha()
        self.ruins_bg = pygame.image.load("assets/ruins_bg.png").convert_alpha()
        self.urban_bg = pygame.image.load("assets/urban_bg.png").convert_alpha()

        # --- Load tiles ---
        self.unbreakable_stone = pygame.transform.scale(
            pygame.image.load("assets/stone-black.png").convert_alpha(), (30, 30)
        )
        self.breakable_barrel = pygame.transform.scale(
            pygame.image.load("assets/environment/barrel.png").convert_alpha(), (30, 30)
        )
        self.breakable_bush = pygame.transform.scale(
            pygame.image.load("assets/environment/bush.png").convert_alpha(), (30, 30)
        )
        self.unbreakable_rock = pygame.transform.scale(
            pygame.image.load("assets/environment/black-block-rock.png").convert_alpha(), (30, 30)
        )
        self.breakable_rock = pygame.transform.scale(
            pygame.image.load("assets/environment/rock.png").convert_alpha(), (30, 30)
        )
        self.breakable_diamond = pygame.transform.scale(
            pygame.image.load("assets/environment/diamond.png").convert_alpha(), (30, 30)
        )
        self.breakable_cactus = pygame.transform.scale(
            pygame.image.load("assets/environment/cactus.png").convert_alpha(), (30, 30)
        )
        self.unbreakable_box = pygame.transform.scale(
            pygame.image.load("assets/environment/box.png").convert_alpha(), (30, 30)
        )
        self.heart_image = pygame.transform.scale(
            pygame.image.load("assets/menu_items/heart.png").convert_alpha(), (30, 30)
        )
        self.pause_icon = pygame.transform.scale(
            pygame.image.load("assets/pauseicon.png").convert_alpha(), (30, 30)
        )
        self.breakable_wall = pygame.transform.scale(
            pygame.image.load("assets/environment/wall.png").convert_alpha(), (30, 30)
        )
        self.unbreakable_wall = pygame.transform.scale(
            pygame.image.load("assets/environment/brick.png").convert_alpha(), (30, 30)
        )
        self.blue_cave = pygame.transform.scale(
            pygame.image.load("assets/environment/blue_cave.png").convert_alpha(), (30, 30)
        )
        self.red_cave = pygame.transform.scale(
            pygame.image.load("assets/environment/red_cave.png").convert_alpha(), (30, 30)
        )
        self.bomb_icon = pygame.transform.scale(
            pygame.image.load("assets/bomb.png").convert_alpha(), (30, 30)
        )
        self.trap_image = pygame.transform.scale(
            pygame.image.load("assets/environment/manhole.png").convert_alpha(), (config.GRID_SIZE, config.GRID_SIZE)
        )

        self.tile_map = copy.deepcopy(selected_map)
        self.available_powerups = ["bomb_powerup", "range_powerup", "freeze_powerup", "live+_powerup", "shield_powerup"]

        self.load_music()
        self.place_hidden_powerups()


    def place_hidden_powerups(self):
        brick_positions = []
        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                if self.tile_map[y][x] == 2:
                    brick_positions.append((x, y))

        num_powerups = int(len(brick_positions) * config.POWERUP_SPAWNING_RATE)
        selected_bricks = random.sample(brick_positions, min(num_powerups, len(brick_positions)))

        for x, y in selected_bricks:
            powerup_type = random.choice(self.available_powerups)
            self.hidden_powerups[(x, y)] = powerup_type


    def load_music(self):
        self.music_manager.play_music('level', 'level_volume', True)


    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in config.PLAYER1_MOVE_KEYS:
                self.player1.held_down_keys.append(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS:
                self.player2.held_down_keys.append(event.key)
            if event.key == pygame.K_p:
                self.game.state_manager.change_state("Pause", self.selected_map, self.map_name)
        elif event.type == pygame.KEYUP:
            if event.key in config.PLAYER1_MOVE_KEYS and event.key in self.player1.held_down_keys:
                self.player1.held_down_keys.remove(event.key)
            if event.key in config.PLAYER2_MOVE_KEYS and event.key in self.player2.held_down_keys:
                self.player2.held_down_keys.remove(event.key)


    def handle_explosions(self):
        if not self.explosion_group:
            return
        if self.player1.check_hit() and self.player1.get_health() == 0:
            self.music_manager.play_sound("death", "death_volume")
            pygame.mixer_music.stop()
            self.exit_state()
            self.game.state_manager.change_state("GameOver", self.player2.player_id, self.selected_map, self.map_name)
        elif self.player2.check_hit() and self.player2.get_health() == 0:
            self.music_manager.play_sound("death", "death_volume")
            pygame.mixer_music.stop()
            self.exit_state()
            self.game.state_manager.change_state("GameOver", self.player1.player_id, self.selected_map, self.map_name)


    def destroy_tile(self, x, y):
        if self.tile_map[y][x] == 2:
            if (x, y) in self.hidden_powerups:
                powerup_type = self.hidden_powerups[(x, y)]
                powerup = PowerUp(x, y, powerup_type)
                powerup.reveal()
                self.powerup_group.add(powerup)
                del self.hidden_powerups[(x, y)]
            self.tile_map[y][x] = 0


    def check_powerup_collisions(self):
        visible_powerups = [p for p in self.powerup_group.sprites() if not p.hidden]
        for powerup in visible_powerups:
            for player in [self.player1, self.player2]:
                if pygame.sprite.collide_rect(player, powerup):
                    self.powerup_message = powerup.apply_effect(player)
                    self.message_timer = pygame.time.get_ticks()
                    self.music_manager.play_sound("walk", "walk_volume")
                    powerup.kill()


    # --- Draw methods ---
    def draw_menu(self, screen):
        player1_lives_text = self.game.font.render(f"x {self.player1.get_health()}", True, config.COLOR_BLACK)
        player2_lives_text = self.game.font.render(f"x {self.player2.get_health()}", True, config.COLOR_BLACK)
        screen.blit(player1_lives_text, (config.GRID_SIZE, 10))
        screen.blit(player2_lives_text, (config.SCREEN_WIDTH - 3 * config.GRID_SIZE, 10))
        screen.blit(self.heart_image, (0, 0))
        screen.blit(self.heart_image, (config.SCREEN_WIDTH - 4 * config.GRID_SIZE, 0))

        player1_bombs = self.game.font.render(f"x {self.player1.get_max_bombs()}", True, config.COLOR_BLACK)
        player2_bombs = self.game.font.render(f"x {self.player2.get_max_bombs()}", True, config.COLOR_BLACK)
        screen.blit(self.bomb_icon, (config.GRID_SIZE * 2, 0))
        screen.blit(self.bomb_icon, (config.SCREEN_WIDTH - 2 * config.GRID_SIZE, 0))
        screen.blit(player1_bombs, (config.GRID_SIZE * 3, 10))
        screen.blit(player2_bombs, (config.SCREEN_WIDTH - config.GRID_SIZE, 10))

        self.draw_active_powerups(screen)

        if self.powerup_message:
            message_text = self.game.font.render(self.powerup_message, True, config.COLOR_BLACK)
            screen.blit(message_text, (config.SCREEN_WIDTH // 2 - message_text.get_width() // 2, 10))


    def draw_active_powerups(self, screen):
        p1_texts, p2_texts = [], []
        for powerup, expire in self.player1.active_powerups.items():
            remaining = round(expire - time.time(), 2)
            if remaining > 0:
                if powerup == "shield_powerup": p1_texts.append(f"Shield: {remaining}s")
                elif powerup == "freeze_powerup": p2_texts.append(f"Freeze: {remaining}s")
        for powerup, expire in self.player2.active_powerups.items():
            remaining = round(expire - time.time(), 2)
            if remaining > 0:
                if powerup == "shield_powerup": p2_texts.append(f"Shield: {remaining}s")
                elif powerup == "freeze_powerup": p1_texts.append(f"Freeze: {remaining}s")

        y = 40
        for text in p1_texts:
            screen.blit(self.game.font.render(text, True, config.COLOR_BLACK), (10, y))
            y += 20
        y = 40
        for text in p2_texts:
            rendered = self.game.font.render(text, True, config.COLOR_BLACK)
            screen.blit(rendered, (config.SCREEN_WIDTH - rendered.get_width() - 10, y))
            y += 20


    def draw_grid(self, screen):
        if self.map_name == "Crystal Caves": screen.blit(self.cave_bg, (0, 0))
        elif self.map_name == "Classic": screen.blit(self.grass_bg, (0, 0))
        elif self.map_name == "Desert Maze": screen.blit(self.sand_bg, (0, 0))
        elif self.map_name == "Ancient Ruins": screen.blit(self.ruins_bg, (0, 0))
        elif self.map_name == "Urban Assault": screen.blit(self.urban_bg, (0, 0))
        else:
            for line in range((config.SCREEN_WIDTH // config.GRID_SIZE) + 1):
                pygame.draw.line(screen, config.COLOR_BLACK, (line * config.GRID_SIZE, 30),
                                 (line * config.GRID_SIZE, config.SCREEN_HEIGHT))
            for line in range((config.SCREEN_HEIGHT // config.GRID_SIZE) - 1):
                pygame.draw.line(screen, config.COLOR_BLACK, (0, line * config.GRID_SIZE + 30),
                                 (config.SCREEN_WIDTH, line * config.GRID_SIZE + 30))


    def draw_walls(self, screen):
        for y, row in enumerate(self.tile_map):
            for x, tile in enumerate(row):
                px, py = x * config.GRID_SIZE, y * config.GRID_SIZE
                if tile in [0, 4, 5]:
                    if self.map_name not in ["Crystal Caves", "Desert Maze", "Classic", "Ancient Ruins", "Urban Assault"]:
                        rect = pygame.Rect(px, py, config.GRID_SIZE, config.GRID_SIZE)
                        color = config.COLOR_DARK_GREEN if (x + y) % 2 == 0 else config.COLOR_LIGHT_GREEN
                        pygame.draw.rect(screen, color, rect)
                elif tile == 1:
                    if self.map_name == "Crystal Caves": screen.blit(self.unbreakable_stone, (px, py))
                    elif self.map_name in ["Classic", "Desert Maze"]: screen.blit(self.unbreakable_box, (px, py))
                    elif self.map_name == "Ancient Ruins": screen.blit(self.unbreakable_rock, (px, py))
                    else: screen.blit(self.unbreakable_wall, (px, py))
                elif tile == 2:
                    if self.map_name == "Desert Maze": screen.blit(self.breakable_cactus, (px, py))
                    elif self.map_name == "Classic": screen.blit(self.breakable_bush, (px, py))
                    elif self.map_name == "Crystal Caves": screen.blit(self.breakable_diamond, (px, py))
                    elif self.map_name == "Ancient Ruins": screen.blit(self.breakable_rock, (px, py))
                    else: screen.blit(self.breakable_wall, (px, py))
                if tile == 4: screen.blit(self.blue_cave, (px, py))
                if tile == 5: screen.blit(self.red_cave, (px, py))
                elif tile == config.TRAP: screen.blit(self.trap_image, (px, py))


    def draw_players(self, screen):
        for player in [self.player1, self.player2]:
            # --- Hráč ---
            screen.blit(player.image, player.rect)

            # --- Čiapka podľa skinu ---
            if player.skin:
                hat_name = player.hat
                if hat_name and hat_name != "None":
                    # HATS obsahuje offset pre hru
                    hat_def = next((h for h in HATS if h["name"] == hat_name), None)
                    if hat_def:
                        hat_img = self.hat_images[hat_name]
                        if hat_img:
                            ox, oy = hat_def.get("offset", (0,0))  # offset pre hru

                            # --- Špeciálne posuny pre "Devil" rohy ---
                            if hat_name == "Devil":
                                if not hasattr(self, 'game_corner_offset'):
                                    self.game_corner_offset = {1: 10, 2: -10}
                                ox += self.game_corner_offset.get(player.player_id, 0)

                            hx = player.rect.x
                            hy = player.rect.y

                            # Flip pre hráča 2
                            if player.player_id == 2:
                                hat_img = pygame.transform.flip(hat_img, True, False)

                            screen.blit(hat_img, (hx, hy))


    def update(self):
        now = pygame.time.get_ticks()
        self.player1.moving = False
        self.player2.moving = False
        self.player1.handle_queued_keys(now)
        self.player2.handle_queued_keys(now)
        self.player1.update_animation()
        self.player2.update_animation()
        self.handle_explosions()
        self.check_powerup_collisions()
        self.player1.update_powerups()
        self.player2.update_powerups()
        self.powerup_group.update()
        self.check_trap_collisions()
        if self.message_timer > 0 and now - self.message_timer > 3000:
            self.powerup_message = ""
            self.message_timer = 0


    def check_trap_collisions(self):
        for player in self.players:
            grid_x = player.rect.x // config.GRID_SIZE
            grid_y = player.rect.y // config.GRID_SIZE
            if (0 <= grid_y < len(self.tile_map)) and (0 <= grid_x < len(self.tile_map[0])) and self.tile_map[grid_y][grid_x] == config.TRAP:
                current_time = time.time()
                if not hasattr(player, 'last_trap_time') or current_time - player.last_trap_time > 1.0:
                    player.health = max(0, player.health - 1)
                    player.last_trap_time = current_time
                    if player.health <= 0:
                        self.music_manager.play_sound("death", "death_volume")
                        pygame.mixer_music.stop()
                        self.exit_state()
                        winner = self.player2.player_id if player.player_id == 1 else self.player1.player_id
                        self.game.state_manager.change_state("GameOver", winner, self.selected_map, self.map_name)
                    else:
                        self.music_manager.play_sound("death", "death_volume")
                        self.powerup_message = f"Player {player.player_id} fell in a sewer!"
                        self.message_timer = pygame.time.get_ticks()


    def render(self, screen):
        screen.fill(config.COLOR_WHITE)
        self.draw_grid(screen)
        self.draw_walls(screen)
        self.draw_menu(screen)
        self.draw_players(screen)
        self.bomb_group.update(self.explosion_group)
        self.explosion_group.update()
        self.powerup_group.draw(screen)
        self.bomb_group.draw(screen)
        self.explosion_group.draw(screen)


#TO DO: čiapky sa nezobrazujú v main loope len v skin selectore