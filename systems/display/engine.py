# display/engine.py
import os
import pygame
import pygame_gui

from .theme  import ThemeColors

from .screens.title import TitleScreen

class DisplayEngine:
    def __init__(self, config, registry):
        pygame.init()
        self.config = config
        self.registry = registry

        self.window_size = (config.options.width, config.options.height)
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Branly's Gambit")

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        theme_path = os.path.join(base_dir, "data", "theme.json")

        self.ui = pygame_gui.UIManager(
            self.window_size,
            theme_path="data/theme.json"
        )

        self.theme = ThemeColors(self.ui)

        self.clock = pygame.time.Clock()
        self.active_screen = None
        self.set_screen(TitleScreen)

    def set_screen(self, screen_cls):
        if self.active_screen:
            self.active_screen.on_exit()
        self.ui.clear_and_reset()
        self.active_screen = screen_cls(self)
        self.active_screen.on_enter()

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                self.ui.process_events(event)
                self.active_screen.process_event(event)

            self.ui.update(dt)
            self.active_screen.update(dt)

            self.screen.fill((0, 0, 0))
            self.active_screen.draw(self.screen)
            self.ui.draw_ui(self.screen)
            pygame.display.flip()

    def _load_image(self, path: str | None, fallback=(40, 40, 40), size=None, flip=False):
        surf = pygame.Surface(size or (240, 240), pygame.SRCALPHA)
        surf.fill(fallback)
        path = f"assets/textures/{path}" if path and not os.path.isabs(path) else path
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                if size:
                    img = pygame.transform.smoothscale(img, size)
                if flip:
                    img = pygame.transform.flip(img, True, False)
                return img
            except pygame.error:
                pass
        return surf
    
    def _invert_surface(self, surface: pygame.Surface) -> pygame.Surface:
        inverted = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        px = pygame.PixelArray(surface.copy())

        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                inverted.set_at((x, y), (255 - r, 255 - g, 255 - b, a))

        return inverted


def create_engine(display_config, registry):
    return DisplayEngine(display_config, registry)