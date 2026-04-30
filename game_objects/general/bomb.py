import pygame
import config, os
import time
from managers.music_manager import MusicManager


class Bomb(pygame.sprite.Sprite):
    def __init__(self, player, bomb_group, explosion_group, test_field, bomb_skin=None, explosion_skin=None):
        super().__init__()
        self.bomb_skin = bomb_skin if bomb_skin is not None else getattr(player, "bomb_skin", "Classic")
        self.explosion_skin = explosion_skin if explosion_skin is not None else getattr(player, "explosion_skin", "Classic")
        self.test_field = test_field
        self.music_manager = MusicManager()

        # najdi bombu v config.BOMBS podľa bomb_skin
        bomb_data = next((b for b in config.BOMBS if b["name"] == self.bomb_skin), None)

        if bomb_data:
            path = os.path.join("assets", "player_bombs", bomb_data["file"])
        else:
            path = os.path.join("assets", "player_bombs", "classic_bomb.png")

        self.image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (config.GRID_SIZE, config.GRID_SIZE))
        # nastav pozíciu bomby na pozíciu hráča
        self.rect = self.image.get_rect()
        self.rect.topleft = player.rect.topleft

        # vlastnosti bomby
        self.range = player.power  # rozsah výbuchu 
        self.player = player
        self.fuse_time = time.time() + 3  # bomba exploduje po 3 sekundách
        self.explosion_group = explosion_group
        # pridaj bombu do skupiny bomb
        bomb_group.add(self)
        self.passable = False

    def update(self, explosion_group):
        """Update method to check if the bomb should explode."""
        if time.time() >= self.fuse_time:
            self.explode(explosion_group)

    def explode(self, explosion_group):
        """Handles the bomb explosion and removes it from the game."""
        self.music_manager.play_sound("explosion", "explosion_volume")

        # CENTER explosion
        x = self.rect.x
        y = self.rect.y
        Explosion(x, y, explosion_group, 0, self.test_field, self.explosion_skin)

        # Nastavenie smerov výbuchu: vpravo, vľavo, hore, dole
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for dx, dy in directions:
            for distance in range(1, self.range + 1):

                x = self.rect.x + dx * distance * config.GRID_SIZE
                y = self.rect.y + dy * distance * config.GRID_SIZE

                tile_x = x // config.GRID_SIZE
                tile_y = y // config.GRID_SIZE

                max_x = (config.SCREEN_WIDTH - config.GRID_SIZE) // config.GRID_SIZE
                max_y = (config.SCREEN_HEIGHT - config.GRID_SIZE) // config.GRID_SIZE

                if not (0 <= tile_x <= max_x and 0 <= tile_y <= max_y):
                    break

                tile_type = self.test_field.tile_map[tile_y][tile_x]

                if tile_type == 0:
                    Explosion(x, y, explosion_group, 0, self.test_field, self.explosion_skin)

                elif tile_type == 1:
                    break

                elif tile_type == 2:
                    self.test_field.destroy_tile(tile_x, tile_y)
                    Explosion(x, y, explosion_group, 0, self.test_field, self.explosion_skin)
                    break

                elif tile_type in [4, 5]:
                    break

                elif tile_type in [6, 7]:
                    Explosion(x, y, explosion_group, 0, self.test_field, self.explosion_skin)
                    break
        
        # povolí hráčovi položiť ďalšiu bombu
        self.player.currentBomb += 1
        
        # odstráni bombu zo skupiny a z hry
        self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, explosion_group, explosion_range, test_field, explosion_skin="Classic"):
        super().__init__()

        self.test_field = test_field
        skin = explosion_skin.lower()
        self.image_a = pygame.image.load(f"assets/player_explosions/{skin}_a.png").convert_alpha()
        self.image_c = pygame.image.load(f"assets/player_explosions/{skin}_c.png").convert_alpha()

        # zväčši obrázky výbuchu na veľkosť GRID_SIZE
        self.image_a = pygame.transform.scale(self.image_a, (config.GRID_SIZE, config.GRID_SIZE))
        self.image_c = pygame.transform.scale(self.image_c, (config.GRID_SIZE, config.GRID_SIZE))

        # nastav počiatočný obrázok výbuchu
        self.image = self.image_a
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        # časovač pre zmenu obrázku výbuchu a jeho odstránenie
        self.start_time = time.time()
        self.switch_time = self.start_time + 0.25  # prestup na image_c po 0.25s
        self.lifetime = 0.5  # odstráni výbuch po 0.5s

        explosion_group.add(self)

        # vytvorí výbuchy v okolí bomby podľa explosion_range
        if explosion_range > 0:
            self.create_explosions(x, y, explosion_group, explosion_range)
    def create_explosions(self, x, y, explosion_group, explosion_range):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # vlavo, vpravo, dole, hore
        for dx, dy in directions:
            for i in range(1, explosion_range + 1):
                tile_x = (x + dx * config.GRID_SIZE * i) // config.GRID_SIZE
                tile_y = (y + dy * config.GRID_SIZE * i) // config.GRID_SIZE

                max_x = (config.SCREEN_WIDTH - config.GRID_SIZE) // config.GRID_SIZE
                max_y = (config.SCREEN_HEIGHT - config.GRID_SIZE) // config.GRID_SIZE

                new_x = tile_x * config.GRID_SIZE
                new_y = tile_y * config.GRID_SIZE
                if not (0 <= tile_x <= max_x and 0 <= tile_y <= max_y):
                    break
                elif self.test_field.tile_map[tile_y][tile_x] == 0:
                    explosion = Explosion(new_x, new_y, explosion_group, 0, self.test_field, self.explosion_skin)
                    explosion_group.add(explosion)
                elif self.test_field.tile_map[tile_y][tile_x] == 2:
                    self.test_field.destroy_tile(tile_x, tile_y)
                    explosion = Explosion(new_x, new_y, explosion_group, 0, self.test_field, self.explosion_skin)
                    explosion_group.add(explosion)
                    break  # zastaví výbuch v tomto smere po zničení tehly
                elif self.test_field.tile_map[tile_y][tile_x] == 4:
                    break
                elif self.test_field.tile_map[tile_y][tile_x] == 5:
                    break
                elif self.test_field.tile_map[tile_y][tile_x] == 1:  # Wall
                    break  # zastaví výbuch v tomto smere
                elif self.test_field.tile_map[tile_y][tile_x] in [6, 7]:  
                    explosion = Explosion(new_x, new_y, explosion_group, 0, self.test_field, self.explosion_skin)
                    explosion_group.add(explosion)
                    break  # zastaví výbuch v tomto smere

    def update(self):
        """Remove explosion after lifetime expires."""
        current_time = time.time()
        # nastaví obrázok výbuchu na image_c po uplynutí switch_time
        if current_time >= self.switch_time and self.image != self.image_c:
            self.image = self.image_c

        # odstráni výbuch po uplynutí lifetime
        if current_time - self.start_time > self.lifetime:
            self.kill()