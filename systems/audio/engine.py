import os
import pygame

from core.registry import SystemRegistry
from .schema import AudioConfig

class AudioEngine:
    def __init__(self, config: AudioConfig):
        self.config = config
        self.sound_cache = {}

        if config.enabled:
            pygame.mixer.init()

        pygame.mixer.music.set_volume(config.music_volume)

    def play_move(self, move):
        if not self.config.enabled:
            return

        if not move or not move.sound:
            return

        path = move.sound
        if not os.path.exists(path):
            return

        if path not in self.sound_cache:
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self.config.sfx_volume * self.config.master_volume)
                self.sound_cache[path] = snd
            except pygame.error:
                return

        self.sound_cache[path].play()

    def play_path(self, path: str | None):
        if not self.config.enabled or not path:
            return

        if path not in self.sound_cache:
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self.config.sfx_volume * self.config.master_volume)
                self.sound_cache[path] = snd
            except pygame.error:
                return

        self.sound_cache[path].play()


def create_engine(config: AudioConfig, registry : SystemRegistry):
    return AudioEngine(config)
