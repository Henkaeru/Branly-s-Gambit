# @ Audio configuration
from dataclasses import dataclass

@dataclass(frozen=True)
class AudioConfig:
    MASTER_VOLUME: float = 0.8
    MUSIC_VOLUME: float = 0.6
    SFX_VOLUME: float = 0.8

    MENU_THEME: str = "audio/menu_theme.mp3"
    BATTLE_THEME: str = "audio/battle_theme.mp3"
    VICTORY_THEME: str = "audio/victory_theme.mp3"

    HIT_SOUND: str = "audio/hit.wav"
    LEVEL_UP: str = "audio/level_up.wav"
