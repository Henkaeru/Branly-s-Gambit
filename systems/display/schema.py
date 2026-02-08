from pydantic import Field, model_validator
from typing import Optional
from core.dsl.resolvable import ResolvableModel
from core.dsl.random_dsl import check

class DisplayOptions(ResolvableModel):
    width: int = 1280
    height: int = 720
    fullscreen: bool = False
    master_volume: float = 0.8
    title_screen_background_sprite: Optional[str] = "backgrounds/default_title.png"
    character_selection_screen_background_sprite: Optional[str] = "backgrounds/default_character_selection.png"
    battle_screen_background_sprite: Optional[str] = "backgrounds/default_battle.png"
    battle_screen_music: Optional[str] = None
    log_height: int = 140
    move_height: int = 140

    @model_validator(mode="after")
    def clamp(self):
        check("width >= 640", width=self.width)
        check("height >= 480", height=self.height)
        self.master_volume = max(0.0, min(1.0, float(self.master_volume)))
        self.log_height = max(80, self.log_height)
        self.move_height = max(100, self.move_height)
        return self

class DisplayConfig(ResolvableModel):
    options: DisplayOptions = Field(default_factory=DisplayOptions)
