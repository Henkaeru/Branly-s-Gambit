from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ColorVariant:
    base: str
    light: Optional[str] = None
    dark: Optional[str] = None
    accent: Optional[str] = None


@dataclass
class Palette:
    primary: ColorVariant
    secondary: ColorVariant
    success: ColorVariant
    warning: ColorVariant
    error: ColorVariant
    info: ColorVariant
    neutral: ColorVariant
    background: ColorVariant
    surface: ColorVariant
    outline: ColorVariant


@dataclass
class LayerColors:
    """Colors scoped to a specific visual layer or theme region."""
    header: ColorVariant
    body: ColorVariant
    footer: ColorVariant
    overlay: ColorVariant
    border: ColorVariant
    highlight: ColorVariant
    shadow: ColorVariant


@dataclass
class ThemeColors:
    """Top-level grouping by theme (light, dark, etc)."""
    name: str
    palette: Palette
    layers: LayerColors
    semantic_overrides: Dict[str, str] = field(default_factory=dict)


@dataclass
class ColorConfig:
    """Global color configuration with extension and override support."""
    themes: Dict[str, ThemeColors]
    default_theme: str = "light"
    mode_sync: bool = True  # automatically sync to system dark/light mode

    def get_theme(self, name: Optional[str] = None) -> ThemeColors:
        return self.themes.get(name or self.default_theme)

    def extend_theme(self, base_name: str, new_name: str, overrides: Dict[str, str]):
        """Create a new theme based on an existing one, applying overrides."""
        base = self.themes[base_name]
        extended = ThemeColors(
            name=new_name,
            palette=base.palette,
            layers=base.layers,
            semantic_overrides={**base.semantic_overrides, **overrides}
        )
        self.themes[new_name] = extended
        return extended
