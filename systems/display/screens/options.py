import pygame
import pygame_gui
from pygame_gui.elements import UILabel, UIHorizontalSlider, UIButton


from .base import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .title import TitleScreen

class OptionsScreen(Screen):
    def on_enter(self):
        w, h = self.engine.window_size

        UILabel((w//2 - 100, h//2 - 120), "Master Volume", self.ui)

        self.volume = UIHorizontalSlider(
            relative_rect=pygame.Rect((w//2 - 100, h//2 - 80), (200, 25)),
            start_value=self.engine.config.master_volume,
            value_range=(0.0, 1.0),
            manager=self.ui
        )

        self.back = UIButton(
            pygame.Rect((w//2 - 80, h//2 + 80), (160, 40)),
            "Back",
            self.ui
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.volume:
                self.engine.config.master_volume = event.value

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back:
                from .title import TitleScreen
                self.engine.set_screen(TitleScreen)

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def on_exit(self):
        pass
