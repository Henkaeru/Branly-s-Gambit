import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIImage


from .base import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .char_select import CharacterSelectScreen
    from .options import OptionsScreen

class TitleScreen(Screen):
    def __init__(self, engine):
        super().__init__(engine)
        self.ui_on_top = True
        # store decorative UI elements so they can be referenced/cleaned if needed
        self._decor = []

    def on_enter(self):
        w, h = self.engine.window_size

        # load title screen background from config (optional)
        bg_path = getattr(self.engine.config.options, "title_screen_background_sprite", None)
        self._bg = self.engine._load_image(bg_path, size=self.engine.window_size)

        # larger, cooler buttons: wider/taller and decorative rounded-rect backs
        btn_w, btn_h = 360, 90
        spacing_y = 24
        start_y = h // 2 - 80

        # create decorative backs first so buttons render above them
        def make_decor(rect):
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            # background panel
            pygame.draw.rect(s, (12, 12, 12, 200), s.get_rect(), border_radius=14)
            # inner glow strip
            inner = s.get_rect().inflate(-6, -10)
            pygame.draw.rect(s, (40, 40, 60, 140), inner, border_radius=12)
            # subtle border
            pygame.draw.rect(s, (120, 120, 140, 30), s.get_rect(), width=2, border_radius=14)
            return s

        # Play button decor + button
        play_rect = pygame.Rect((w//2 - btn_w//2, start_y - 10), (btn_w, btn_h))
        play_back = UIImage(relative_rect=play_rect, image_surface=make_decor(play_rect), manager=self.ui)
        self._decor.append(play_back)
        # clickable UIButton but with empty text (we render a larger label as UIImage)
        self.play_btn = UIButton(relative_rect=play_rect, text="", manager=self.ui)
        # large label image
        btn_font = pygame.font.SysFont(None, 48, bold=True)
        txt = "Play"
        shadow = btn_font.render(txt, True, (0, 0, 0))
        main = btn_font.render(txt, True, (255, 245, 200))
        label_surf = pygame.Surface(play_rect.size, pygame.SRCALPHA)
        lx = (play_rect.width - main.get_width()) // 2
        ly = (play_rect.height - main.get_height()) // 2
        label_surf.blit(shadow, (lx + 3, ly + 3))
        label_surf.blit(main, (lx, ly))
        lbl = UIImage(relative_rect=play_rect, image_surface=label_surf, manager=self.ui)
        self._decor.append(lbl)

        # Options
        opt_rect = pygame.Rect((w//2 - btn_w//2, start_y + btn_h + spacing_y - 10), (btn_w, btn_h))
        opt_back = UIImage(relative_rect=opt_rect, image_surface=make_decor(opt_rect), manager=self.ui)
        self._decor.append(opt_back)
        self.options_btn = UIButton(relative_rect=opt_rect, text="", manager=self.ui)
        txt = "Options"
        shadow = btn_font.render(txt, True, (0, 0, 0))
        main = btn_font.render(txt, True, (255, 245, 200))
        label_surf = pygame.Surface(opt_rect.size, pygame.SRCALPHA)
        lx = (opt_rect.width - main.get_width()) // 2
        ly = (opt_rect.height - main.get_height()) // 2
        label_surf.blit(shadow, (lx + 3, ly + 3))
        label_surf.blit(main, (lx, ly))
        lbl = UIImage(relative_rect=opt_rect, image_surface=label_surf, manager=self.ui)
        self._decor.append(lbl)

        # Quit
        quit_rect = pygame.Rect((w//2 - btn_w//2, start_y + (btn_h + spacing_y) * 2 - 10), (btn_w, btn_h))
        quit_back = UIImage(relative_rect=quit_rect, image_surface=make_decor(quit_rect), manager=self.ui)
        self._decor.append(quit_back)
        self.quit_btn = UIButton(relative_rect=quit_rect, text="", manager=self.ui)
        txt = "Quit"
        shadow = btn_font.render(txt, True, (0, 0, 0))
        main = btn_font.render(txt, True, (255, 245, 200))
        label_surf = pygame.Surface(quit_rect.size, pygame.SRCALPHA)
        lx = (quit_rect.width - main.get_width()) // 2
        ly = (quit_rect.height - main.get_height()) // 2
        label_surf.blit(shadow, (lx + 3, ly + 3))
        label_surf.blit(main, (lx, ly))
        lbl = UIImage(relative_rect=quit_rect, image_surface=label_surf, manager=self.ui)
        self._decor.append(lbl)

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
        # draw configured background if available
        if getattr(self, "_bg", None):
            surface.blit(self._bg, (0, 0))

        # decorative banner/backs are UIImage elements in the UI manager, UI will draw them.
        # here we can add subtle animated overlay if desired (kept minimal).

    def on_exit(self):
        # allow GC of background surface and clear decor refs
        try:
            self._bg = None
        except Exception:
            pass
        try:
            self._decor.clear()
        except Exception:
            pass
