# @ Audio configuration
from dataclasses import dataclass

@dataclass(frozen=True)
class AudioConfig:
    MASTER_VOLUME: float = 0.8
    MUSIC_VOLUME: float = 0.6
    SFX_VOLUME: float = 0.8

    MENU_THEME: str = "audio/menu_theme.ogg"
    BATTLE_THEME: str = "audio/battle_theme.ogg"
    VICTORY_THEME: str = "audio/victory_theme.ogg"

    HIT_SOUND: str = "audio/hit.ogg"
    LEVEL_UP: str = "audio/level_up.ogg"
