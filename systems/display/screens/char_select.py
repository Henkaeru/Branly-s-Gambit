import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from systems.battle.schema import Battle

from .base import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import BattleScreen


class CharacterSelectScreen(Screen):
    def on_enter(self):
        self.player = 1
        self.p1_fighter = None
        self.p2_fighter = None

        fighters = self.engine.registry.get("fighters").set.values()
        self.buttons = []

        # layout params
        start_x, x, y = 120, 120, 80
        btn_w, btn_h = 180, 200
        spacing_x, spacing_y = 20, 20

        # determine available width (fallback to 800)
        surface = pygame.display.get_surface()
        max_width = surface.get_width() if surface else 800
        right_limit = max_width - 40

        for fighter in fighters:
            # wrap to next line if the button would overflow
            if x + btn_w > right_limit:
                x = start_x
                y += btn_h + spacing_y

            # create button without builtin text so it doesn't draw under the sprite
            btn = UIButton(
                relative_rect=pygame.Rect((x, y), (btn_w, btn_h)),
                text="",  # <- disable default label
                manager=self.ui,
                object_id=f"#fighter_{fighter.id}"
            )
            btn.fighter_id = fighter.id
            # store reference to fighter and load selection sprite
            btn.fighter = fighter
            btn.selection_sprite = self.engine._load_image(
                getattr(fighter, "fighter_selection_sprite", None),
                fallback=(60, 60, 60),
                size=(btn_w - 20, btn_h - 60)
            )
            # keep name separate for custom label rendering
            btn.display_name = getattr(fighter, "name", "")
            self.buttons.append(btn)
            x += btn_w + spacing_x

        # prepare label font (larger/bolder for readability)
        self._label_font = pygame.font.SysFont(None, 18, bold=True)

        # load background for character selection screen
        bg_path = getattr(self.engine.config.options, "character_selection_screen_background_sprite", None)
        self._bg = self.engine._load_image(bg_path, size=self.engine.window_size)

        # load highlight image and precompute inverted copy (used instead of rect outlines)
        hl_path = "icons/char_select.png"
        # request a slightly larger size than the button to act as an outline (will be scaled per-button)
        self._hl_src = self.engine._load_image(hl_path, size=(btn_w + 12, btn_h + 12)) if 'btn_w' in locals() else self.engine._load_image(hl_path)
        try:
            self._hl_inv_src = self.engine._invert_surface(self._hl_src)
        except Exception:
            self._hl_inv_src = self._hl_src.copy()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            fighter_id = getattr(event.ui_element, "fighter_id", None)
            if not fighter_id:
                return
            
            if self.player == 1:
                self.p1_fighter = fighter_id
                self.player = 2
            elif self.player == 2:
                self.p2_fighter = fighter_id
                self._start_battle()

    def _start_battle(self):
        fighters = self.engine.registry.get("fighters").set

        left = fighters.get(self.p1_fighter)
        right = fighters.get(self.p2_fighter)

        battle = Battle.from_sides(
            id="1v1_match",
            sides = [[left.id], [right.id]],
            background_sprite=self.engine.config.options.battle_screen_background_sprite,
            music=self.engine.config.options.battle_screen_music
        )
        battle_engine = self.engine.registry.get("battle")
        battle_engine.start(battle)

        from .battle import BattleScreen
        self.engine.set_screen(BattleScreen)

    def update(self, dt):
        pass

    def draw(self, surface):
        # draw background if available
        if getattr(self, "_bg", None):
            surface.blit(self._bg, (0, 0))

        # determine selection highlight color (fallback to yellow)
        hl_col = getattr(self.engine.config.options, "selection_highlight_color", None)
        if hl_col is None:
            sel_color = pygame.Color(255, 255, 0)
        else:
            sel_color = pygame.Color(*hl_col) if isinstance(hl_col, (list, tuple)) else pygame.Color(hl_col)

        # helper to invert a color
        def invert_color(c: pygame.Color) -> pygame.Color:
            return pygame.Color(255 - c.r, 255 - c.g, 255 - c.b, c.a)

        # determine hover color (fallback to selection color)
        hover_cfg = getattr(self.engine.config.options, "hover_highlight_color", None)
        if hover_cfg is None:
            hover_color = sel_color
        else:
            hover_color = pygame.Color(*hover_cfg) if isinstance(hover_cfg, (list, tuple)) else pygame.Color(hover_cfg)

        # if it's player 2's turn, invert the hover color
        hover_color_for_turn = invert_color(hover_color) if getattr(self, "player", 1) == 2 else hover_color

        mouse_pos = pygame.mouse.get_pos()

        # first draw sprites and labels inside each button box
        for btn in getattr(self, "buttons", []):
            # draw sprite centered in the button leaving space at bottom for label
            img = getattr(btn, "selection_sprite", None)
            inner_rect = btn.relative_rect.inflate(-10, -40)
            if img:
                # center the image inside inner_rect
                img_w, img_h = img.get_size()
                x = inner_rect.x + max(0, (inner_rect.width - img_w) // 2)
                y = inner_rect.y + max(0, (inner_rect.height - img_h) // 2)
                surface.blit(img, (x, y))

            # draw refined label at bottom of button
            fighter_name = getattr(btn, "display_name", "")
            if fighter_name:
                name = fighter_name.title()
                # use simple ASCII decorations to avoid glyph issues
                text = f"{name}"

                # render text and shadow
                text_surf = self._label_font.render(text, True, (255, 255, 255))
                shadow_surf = self._label_font.render(text, True, (0, 0, 0))

                label_w, label_h = text_surf.get_size()
                label_x = btn.relative_rect.x + (btn.relative_rect.width - label_w) // 2
                label_y = btn.relative_rect.bottom - label_h - 30

                # choose base color from selection highlight (fallback to dark gray)
                hl_col = getattr(self.engine.config.options, "selection_highlight_color", None)
                if hl_col is None:
                    base_col = pygame.Color(40, 40, 40, 210)
                    border_col = (200, 200, 200)
                else:
                    base = pygame.Color(*hl_col) if isinstance(hl_col, (list, tuple)) else pygame.Color(hl_col)
                    # darken base color for background and set alpha
                    base_col = pygame.Color(max(0, base.r - 60), max(0, base.g - 60), max(0, base.b - 60), 200)
                    border_col = (min(255, base.r + 40), min(255, base.g + 40), min(255, base.b + 40))

                # background with rounded corners and subtle border
                bg_w, bg_h = label_w + 16, label_h + 10
                bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, base_col, bg_surf.get_rect(), border_radius=8)
                pygame.draw.rect(bg_surf, border_col, bg_surf.get_rect(), width=2, border_radius=8)

                # blit background, shadow and text
                surface.blit(bg_surf, (label_x - 8, label_y - 5))
                surface.blit(shadow_surf, (label_x + 1, label_y + 1))
                surface.blit(text_surf, (label_x, label_y))

        # then draw selection/hover outlines using the highlight image (not rects)
        for btn in getattr(self, "buttons", []):
            bid = getattr(btn, "fighter_id", None)
            hl_src = getattr(self, "_hl_src", None)
            hl_inv = getattr(self, "_hl_inv_src", None)

            # position the icon centered above the fighter image area
            inner = btn.relative_rect.inflate(-10, -40)
            # icon size: clamp to a sensible range relative to button
            icon_px = max(128, min(128, inner.height // 3))
            icon_size = (icon_px, icon_px)
            icon_center_x = btn.relative_rect.centerx
            icon_center_y = inner.y # sit slightly above the sprite area

            def blit_icon(src, center_pos):
                if not src:
                    return
                try:
                    img = pygame.transform.smoothscale(src, icon_size)
                    pos = (center_pos[0] - img.get_width() // 2, center_pos[1] - img.get_height() // 2)
                    surface.blit(img, pos)
                except Exception:
                    # silent fallback
                    pass

            # selected player 1 uses normal icon
            if bid is not None and bid == self.p1_fighter:
                blit_icon(hl_src, (icon_center_x, icon_center_y))
            # selected player 2 uses inverted icon
            elif bid is not None and bid == self.p2_fighter:
                blit_icon(hl_inv, (icon_center_x, icon_center_y))
            # hover uses icon for current player's turn (invert when player == 2)
            elif btn.relative_rect.collidepoint(mouse_pos):
                blit_icon(hl_inv if getattr(self, "player", 1) == 2 else hl_src, (icon_center_x, icon_center_y))

    def on_exit(self):
        pass