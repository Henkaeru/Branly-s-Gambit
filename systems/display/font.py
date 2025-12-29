# @ Font configuration
from dataclasses import dataclass
import pygame

@dataclass(frozen=True)
class FontConfig:
    # Default system fonts
    DEFAULT_FONT: str = "consolas"
    UI_FONT: str = "poppins"
    TITLE_FONT: str = "impact"

    # Sizes for various UI elements
    SIZE_SMALL: int = 16       # tooltips, minor text
    SIZE_MEDIUM: int = 24      # normal UI text, menu options
    SIZE_LARGE: int = 36       # big titles, battle notifications
    SIZE_HUGE: int = 48        # end-of-battle banners, KO text
    SIZE_DAMAGE: int = 32      # damage numbers floating over fighters

    # Style flags
    BOLD: bool = False
    ITALIC: bool = False

    # Fonts preloaded (lazy load recommended)
    def get_font(self, font_name=None, size=None, bold=None, italic=None):
        """
        Returns a pygame Font object based on configuration.
        """
        font_name = font_name or self.DEFAULT_FONT
        size = size or self.SIZE_MEDIUM
        bold = bold if bold is not None else self.BOLD
        italic = italic if italic is not None else self.ITALIC

        return pygame.font.SysFont(font_name, size, bold, italic)

    # Quick-access fonts for common use cases
    def menu_font(self):
        return self.get_font(self.UI_FONT, self.SIZE_MEDIUM, bold=True)

    def title_font(self):
        return self.get_font(self.TITLE_FONT, self.SIZE_LARGE, bold=True)

    def dialog_font(self):
        return self.get_font(self.UI_FONT, self.SIZE_SMALL)

    def damage_font(self):
        return self.get_font(self.DEFAULT_FONT, self.SIZE_DAMAGE, bold=True)

    def banner_font(self):
        return self.get_font(self.TITLE_FONT, self.SIZE_HUGE, bold=True, italic=True)
