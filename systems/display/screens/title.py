import pygame
import pygame_gui
from pygame_gui.elements import UIButton


from .base import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .char_select import CharacterSelectScreen
    from .options import OptionsScreen

class TitleScreen(Screen):
    def on_enter(self):
        w, h = self.engine.window_size

        self.play_btn = UIButton(
            relative_rect=pygame.Rect((w//2 - 100, h//2 - 80), (200, 50)),
            text="Play",
            manager=self.ui
        )
        self.options_btn = UIButton(
            relative_rect=pygame.Rect((w//2 - 100, h//2), (200, 50)),
            text="Options",
            manager=self.ui
        )
        self.quit_btn = UIButton(
            relative_rect=pygame.Rect((w//2 - 100, h//2 + 80), (200, 50)),
            text="Quit",
            manager=self.ui
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_btn:
                from .char_select import CharacterSelectScreen
                self.engine.set_screen(CharacterSelectScreen)
            elif event.ui_element == self.options_btn:
                from .options import OptionsScreen
                self.engine.set_screen(OptionsScreen)
            elif event.ui_element == self.quit_btn:
                pygame.quit()
                raise SystemExit

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def on_exit(self):
        pass
