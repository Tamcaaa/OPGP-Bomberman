import os
import config
import pygame


class MusicManager:
    def __init__(self):
        self.music = {
            "title": "assets/sounds/title.mp3",
            "game_over": "assets/sounds/game_over.mp3",
            "level": "assets/sounds/level.mp3",
            "pause": "assets/sounds/pausemusic.mp3"
        }
        self.sounds = {
            "explosion": "assets/sounds/explosion.mp3",
            "walk": "assets/sounds/walk.mp3",
            "hit": "assets/sounds/hit.mp3",
            "death": "assets/sounds/death.wav",
            'move_map_selector': "assets/sounds/move.wav",
            'final_map_selector': "assets/sounds/final.wav"
        }

    def play_music(self, name: str, volume: str | float = 1, loop: int | bool = False):
        try:
            music_file = self.music.get(name, name)
            pygame.mixer.music.load(music_file)
        except (FileNotFoundError, TypeError, pygame.error) as e:
            raise RuntimeError(f"Failed to load music '{name}': {e}")

        if isinstance(loop, bool) and loop:
            loop = -1
        elif isinstance(loop, bool) and not loop:
            loop = 0

        pygame.mixer.music.set_volume(config.MUSIC_VOLUME.get(volume, volume))
        pygame.mixer.music.play(loop)

    def play_sound(self, name: str, volume: int | str = 1):
        try:
            sound_file = self.sounds.get(name, name)
            sound = pygame.mixer.Sound(sound_file)
            sound.set_volume(config.MUSIC_VOLUME.get(volume, volume))
            sound.play()
        except (AttributeError, TypeError, pygame.error) as e:
            raise RuntimeError(f"Failed to play sound '{name}': {e}")
