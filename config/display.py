# @ Display and system configuration
from dataclasses import dataclass

@dataclass(frozen=True)
class DisplayConfig:
    SCREEN_SIZE: tuple[int, int] = (960, 640)
    FPS: int = 60
    WINDOW_TITLE: str = "Branly's Gambit: Rise of the Prof"
    ICON_PATH: str = "assets/ui/icon.png"
