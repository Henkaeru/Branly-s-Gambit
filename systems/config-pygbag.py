from dataclasses import dataclass, field
from typing import Tuple, Dict
import pygame


# -------------------------
# @ AUDIO SETTINGS
# -------------------------
@dataclass(frozen=True)
class AudioConfig:
    TITLE_THEME: str = "title_theme.ogg"
    BATTLE_THEME: str = "battle_theme.ogg"


# -------------------------
# @ CONTROLS SETTINGS
# -------------------------
@dataclass(frozen=True)
class ControlsConfig:
    PLAYER: dict = field(default_factory=lambda: {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "attack_1": pygame.K_1,
        "attack_2": pygame.K_2,
        "attack_3": pygame.K_3,
        "attack_special": pygame.K_4,
    })


# -------------------------
# @ COLOR PALETTES
# -------------------------
@dataclass(frozen=True)
class ColorConfig:
    PALETTES: Dict[str, Dict[str, Tuple[int, int, int]]] = field(default_factory=lambda: {

        # @ NEUTRALS
        "neutrals": {
            "white": (255, 255, 255),
            "off_white": (245, 240, 230),
            "light_grey": (200, 200, 210),
            "grey": (180, 180, 180),
            "mid_grey": (130, 130, 150),
            "dark_grey": (60, 60, 80),
            "black": (15, 15, 20),
            "dark": (30, 30, 30),
        },

        # @ REDS
        "reds": {
            "light": (255, 110, 110),
            "base": (220, 60, 40),
            "dark": (140, 25, 25),
            "crimson": (180, 30, 60),
            "magma": (150, 30, 25),
        },

        # @ ORANGES
        "oranges": {
            "light": (255, 170, 90),
            "base": (255, 140, 50),
            "deep": (230, 100, 30),
            "burnt": (180, 70, 20),
            "amber": (255, 190, 80),
        },

        # @ YELLOWS
        "yellows": {
            "light": (255, 240, 140),
            "base": (255, 210, 70),
            "golden": (240, 190, 50),
            "mustard": (200, 160, 40),
            "sunburst": (255, 210, 70),
        },

        # @ GREENS
        "greens": {
            "light": (160, 255, 160),
            "base": (80, 200, 100),
            "forest": (40, 130, 60),
            "dark": (25, 90, 40),
            "mint": (120, 230, 180),
        },

        # @ CYANS / AQUAS
        "cyans": {
            "light": (180, 255, 255),
            "base": (60, 200, 255),
            "dark": (0, 130, 180),
            "aqua_highlight": (80, 200, 220),
            "teal": (30, 140, 150),
        },

        # @ BLUES
        "blues": {
            "light": (140, 190, 255),
            "base": (60, 140, 200),
            "branly": (40, 100, 200),
            "branly_dark": (25, 60, 120),
            "prof_navy": (10, 25, 70),
            "cyan_flash": (60, 180, 255),
            "royal": (50, 90, 220),
            "deep_sky": (0, 150, 255),
        },

        # @ PURPLES / VIOLETS
        "purples": {
            "light": (190, 150, 255),
            "glow": (120, 80, 220),
            "violet_shadow": (70, 60, 140),
            "dark": (50, 40, 100),
            "magenta": (220, 80, 200),
        },

        # @ BROWNS
        "browns": {
            "light": (210, 170, 120),
            "base": (150, 100, 60),
            "dark": (100, 60, 30),
            "red_brown": (130, 60, 40),
            "sand": (230, 200, 150),
        },
    })


# -------------------------
# @ GLOBAL CONFIG
# -------------------------
@dataclass(frozen=True)
class Config:
    DISPLAY = DisplayConfig()
    FONTS = FontConfig()
    AUDIO = AudioConfig()
    COLORS = ColorConfig()


CONFIG = Config()


# -------------------------
# @ TYPE ALIASES
# -------------------------
RollResult = tuple[int, str]