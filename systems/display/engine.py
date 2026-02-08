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
        # navigation stack of screen classes
        self._screen_stack = []
        # go-back icon resources
        self._go_back_surf = None
        self._go_back_rect = None

        self.set_screen(TitleScreen)

    def set_screen(self, screen_cls, push: bool = True):
        # push current screen class onto stack if requested
        if push and self.active_screen:
            try:
                self._screen_stack.append(self.active_screen.__class__)
            except Exception:
                pass

        if self.active_screen:
            self.active_screen.on_exit()
        self.ui.clear_and_reset()
        self.active_screen = screen_cls(self)
        self.active_screen.on_enter()

        # prepare go-back icon if there's something to go back to and current is not TitleScreen
        if self._screen_stack and not isinstance(self.active_screen, TitleScreen):
            # load icon (small, top-left)
            icon = self._load_icon("icons/go_back.png", size=(40, 40))
            self._go_back_surf = icon
            self._go_back_rect = pygame.Rect(10, 10, 40, 40)
        else:
            self._go_back_surf = None
            self._go_back_rect = None

    def go_back(self):
        # pop previous screen class and navigate to it
        if not self._screen_stack:
            return
        prev = self._screen_stack.pop()
        # set without pushing current
        self.set_screen(prev, push=False)

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                # handle click on go-back icon before forwarding (mouse down)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._go_back_rect and self._go_back_rect.collidepoint(event.pos):
                        # if active screen wants to confirm, let it handle showing confirmation
                        if hasattr(self.active_screen, "request_go_back") and callable(getattr(self.active_screen, "request_go_back")):
                            try:
                                self.active_screen.request_go_back()
                            except Exception:
                                # fallback to immediate go_back
                                self.go_back()
                        else:
                            self.go_back()
                        # consume this click; do not forward to UI/screen
                        continue

                # handle Escape key globally (go back if possible)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self._screen_stack:
                        # if active screen wants to confirm, call it
                        if hasattr(self.active_screen, "request_go_back") and callable(getattr(self.active_screen, "request_go_back")):
                            try:
                                self.active_screen.request_go_back()
                            except Exception:
                                self.go_back()
                        else:
                            self.go_back()
                        # consume so screen doesn't also handle the escape
                        continue

                self.ui.process_events(event)
                self.active_screen.process_event(event)

            self.ui.update(dt)
            self.active_screen.update(dt)

            self.screen.fill((0, 0, 0))
            # draw UI first so screen-specific drawing (sprites/labels/highlights) appears on top
            self.ui.draw_ui(self.screen)
            self.active_screen.draw(self.screen)

            # if the active screen wants UI drawn on top (e.g. BattleScreen), draw it again
            if getattr(self.active_screen, "ui_on_top", False):
                self.ui.draw_ui(self.screen)

            # draw go-back icon on top if available
            if self._go_back_surf and self._go_back_rect:
                try:
                    self.screen.blit(self._go_back_surf, self._go_back_rect.topleft)
                except Exception:
                    pass

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

    def _load_icon(self, path: str | None, fallback=(0, 0, 0, 0), size=(32, 32), flip=False) -> pygame.Surface:
        """Load an icon like _load_image: resolve under assets/textures, scale/flip, return fallback surface on error."""
        # create fallback surface
        surf = pygame.Surface(size or (32, 32), pygame.SRCALPHA)
        # try to fill with provided fallback (supports RGB or RGBA)
        try:
            surf.fill(fallback)
        except Exception:
            # ensure a transparent fallback if fill fails
            surf.fill((0, 0, 0, 0))

        if not path:
            return surf

        full_path = f"assets/textures/{path}" if path and not os.path.isabs(path) else path
        if full_path and os.path.exists(full_path):
            try:
                img = pygame.image.load(full_path).convert_alpha()
                if size:
                    img = pygame.transform.smoothscale(img, size)
                if flip:
                    img = pygame.transform.flip(img, True, False)
                return img
            except pygame.error:
                # fallthrough to return fallback surface
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