import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextBox, UILabel, UIImage

from .base import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .title import TitleScreen

from systems.battle.engine import BattleMode

import math

class BattleScreen(Screen):
    def __init__(self, engine):
        super().__init__(engine)

        self.battle_engine = engine.registry.get("battle")
        self.renderer = BattleRenderer(engine, self.battle_engine)
        self.controller = BattleController(engine, self.battle_engine)

        self.ui_elements = []
        self.move_buttons = []
        # per-button glow UIImage objects (same order as move_buttons)
        self.move_glows = []
        
        self.fighter_name_labels = {}
        self.selected_move_idx = 0
        self.battle_over = False
        self.ui_on_top = True

        # popup fonts
        self._popup_title_font = pygame.font.SysFont(None, 40, bold=True)
        self._popup_sub_font = pygame.font.SysFont(None, 20)

        # popup UI refs
        self._win_panel = None
        self._win_label = None
        self._win_button = None

        # confirmation popup refs
        self._confirm_panel = None
        self._confirm_yes = None
        self._confirm_no = None

        # bigger, brighter font for fighter names
        self._fighter_name_font = pygame.font.SysFont(None, 36, bold=True)

        # small font for status/buff duration overlays
        self._status_font = pygame.font.SysFont(None, 24, bold=True)
        self._last_active_fighter_id = None

    def on_enter(self):
        self._build_ui()
        self.renderer.load_assets()

        self.battle_engine.set_battle_mode(BattleMode.LOCAL_1V1)

    def on_exit(self):
        for el in self.ui_elements:
            el.kill()
        self.ui_elements.clear()

    def _build_ui(self):
        w, h = self.engine.window_size

        self.action_bar = UIPanel(
            relative_rect=pygame.Rect(0, h - 120, w, 120),
            manager=self.ui
        )
        self.ui_elements.append(self.action_bar)

        self.status_bar = UIPanel(
            relative_rect=pygame.Rect(0, 0, 1, 1),
            manager=self.ui
        )
        self.ui_elements.append(self.status_bar)

        self._build_move_buttons()
        self._build_log_box()

    def _build_move_buttons(self):
        # rebuild any existing buttons/glows
        for el in self.move_buttons + getattr(self, "move_glows", []):
            try:
                el.kill()
            except Exception:
                pass

        self.move_buttons.clear()
        self.move_glows.clear()

        ctx = self.battle_engine.battle.current_context
        user = ctx.active_fighter
        moves = self.controller.current_moves(user)

        for i, move in enumerate(moves):
            # create glow image first so it renders under the button
            btn_rect = pygame.Rect(20 + i * 300, 20, 260, 60)
            glow_rect = btn_rect.inflate(12, 12)
            # initial glow surface (transparent)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            # subtle base for later updates (will be replaced per-frame)
            pygame.draw.rect(glow_surf, (0, 0, 0, 0), glow_surf.get_rect())
            glow = UIImage(
                relative_rect=glow_rect,
                image_surface=glow_surf,
                manager=self.ui,
                container=self.action_bar
            )
            # hide by default
            try:
                glow.visible = False
            except Exception:
                pass
            # prevent glow from capturing hover/click, so button tooltips still show
            try:
                glow.set_blocking(False)
            except Exception:
                try:
                    glow.blocking = False
                except Exception:
                    pass
            # also never report hover, so UIManager keeps hovering the button instead
            glow.hover_point = lambda *_args, **_kwargs: False
            self.move_glows.append(glow)
            self.ui_elements.append(glow)

            # create the actual button (on top of glow)
            btn = UIButton(
                relative_rect=btn_rect,
                text=f"{move.name} ({move.charge_usage})",
                manager=self.ui,
                container=self.action_bar
            )
            btn.move_idx = i
            # add tooltip from move description (safe fallback)
            tooltip = getattr(move, "description", None)
            if tooltip:
                try:
                    btn.set_tooltip(tooltip)
                except Exception:
                    try:
                        btn.tool_tip_text = tooltip
                    except Exception:
                        pass
            self.move_buttons.append(btn)
            self.ui_elements.append(btn)

    def _build_log_box(self):
        w, h = self.engine.window_size

        self.log_box = UITextBox(
            html_text="",
            relative_rect=pygame.Rect(0, h - 275, w, 160),
            manager=self.ui
        )
        self.ui_elements.append(self.log_box)

        self.log_box._build_scrollbar_for_oversized_text = lambda x, y: None  # disable scrollbar building

    def update(self, dt):
        self.renderer.update(dt)
        
        self.controller.update_logs(dt)
        logs = self.controller.visible_logs()
        self.log_box.set_text("<br>".join(logs))

        user = None
        moves = []
        try:
            ctx = self.battle_engine.battle.current_context
            user = ctx.active_fighter
            if getattr(self, "_last_active_fighter_id", None) != id(user):
                self._last_active_fighter_id = id(user)
                self._build_move_buttons()
            moves = self.controller.current_moves(user)
        except Exception:
            pass

        # Update move button usability and glow animation
        t = pygame.time.get_ticks() / 1000.0
        for i, btn in enumerate(self.move_buttons):
            move = moves[i] if i < len(moves) else None
            glow = self.move_glows[i] if i < len(self.move_glows) else None

            usable = False
            if move and user:
                try:
                    usable = (user.current_stats.charge >= getattr(move, "charge_usage", 0))
                except Exception:
                    usable = False

            # enable/disable button (grayed out when disabled)
            try:
                if usable:
                    btn.enable()
                else:
                    btn.disable()
            except Exception:
                # best-effort: change text colour fallback
                try:
                    btn.set_text(btn.text)
                except Exception:
                    pass

            # glow handling:
            # - usable special moves ALWAYS glow (bright, larger)
            # - otherwise only the selected move glows
            if glow is not None:
                is_selected = (i == getattr(self, "selected_move_idx", 0))
                is_special = getattr(move, "category", "") == "special" if move is not None else False

                show_glow = usable and (is_special or is_selected)

                if show_glow:
                    # make visible
                    try:
                        glow.visible = True
                    except Exception:
                        pass

                    # pulse alpha and build glow surface
                    pulse = (math.sin(t * 8.0 + i) + 1) / 2
                    # base alpha
                    alpha = int(140 + pulse * 115)

                    # pick color: special uses target_ring, otherwise label_active
                    try:
                        if is_special:
                            col = self.theme.colour("target_ring")
                        else:
                            col = self.theme.colour("label_active")
                        if isinstance(col, (list, tuple)):
                            r, g, b = col[:3]
                        else:
                            c = pygame.Color(col)
                            r, g, b = c.r, c.g, c.b
                    except Exception:
                        # fallbacks
                        if is_special:
                            r, g, b = (120, 200, 255)
                        else:
                            r, g, b = (255, 200, 60)

                    # create glow surface
                    gw, gh = glow.get_relative_rect().size
                    s = pygame.Surface((gw, gh), pygame.SRCALPHA)

                    # compute border radius to avoid circular look (scale with size)
                    border_radius = max(6, min(20, min(gw, gh) // 6))

                    if is_special:
                        # layered rounded-rect halo (outer soft -> inner bright) to make rectangular glow
                        layers = 4
                        for L in range(layers):
                            # outermost layer more transparent, inner layers brighter
                            layer_factor = 1.0 - (L / max(1, layers - 1)) * 0.8
                            layer_alpha = int(alpha * 0.45 * layer_factor)
                            inflate_x = L * 8
                            inflate_y = L * 4
                            rct = s.get_rect().inflate(-inflate_x, -inflate_y)
                            if rct.width > 0 and rct.height > 0:
                                pygame.draw.rect(s, (r, g, b, max(0, layer_alpha)), rct, border_radius=border_radius + (layers - L))
                        # final inner bright panel
                        inner = s.get_rect().inflate(-18, -10)
                        if inner.width > 0 and inner.height > 0:
                            pygame.draw.rect(s, (r, g, b, alpha), inner, border_radius=border_radius)
                    else:
                        # regular selected glow: single rounded rect
                        pygame.draw.rect(s, (r, g, b, alpha), s.get_rect(), border_radius=border_radius)

                    # apply the constructed surface to the UIImage (try set_image then fallback)
                    try:
                        glow.set_image(s)
                    except Exception:
                        try:
                            glow.image_surface = s
                        except Exception:
                            # recreate fallback
                            try:
                                _relative = glow.get_relative_rect()
                            except Exception:
                                _relative = glow.relative_rect if hasattr(glow, "relative_rect") else glow.get_relative_rect()
                            try:
                                glow.kill()
                            except Exception:
                                pass
                            new_glow = UIImage(relative_rect=_relative, image_surface=s, manager=self.ui, container=self.action_bar)
                            self.move_glows[i] = new_glow
                            self.ui_elements.append(new_glow)
                else:
                    # hide glow
                    try:
                        glow.visible = False
                    except Exception:
                        pass

        # when battle finishes, create a one-time win popup
        if self.battle_engine.battle.is_battle_over:
            if not self.battle_over:
                # first frame we detect end
                self.battle_over = True

            # create popup if not already created
            if self._win_panel is None:
                w, h = self.engine.window_size

                # figure out winner fighter (attempt common properties then fallback)
                battle = self.battle_engine.battle
                winner_fv = None
                winner_name = None

                # direct winner object if provided
                winner_obj = getattr(battle, "winner", None) or getattr(battle, "winning_fighter", None) or getattr(battle, "winner_fighter", None)
                if winner_obj is not None:
                    # winner may be FV or raw name; try to detect FV
                    if hasattr(winner_obj, "current_fighter") or hasattr(winner_obj, "current_stats"):
                        winner_fv = winner_obj
                    else:
                        winner_name = getattr(winner_obj, "name", str(winner_obj))

                # fallback: find an FV with hp > 0
                if winner_fv is None:
                    try:
                        for side in getattr(battle.current_context, "sides", []):
                            for fv in side:
                                if getattr(fv, "current_stats", None) and getattr(fv.current_stats, "hp", 0) > 0:
                                    winner_fv = fv
                                    break
                            if winner_fv:
                                break
                    except Exception:
                        winner_fv = None

                if winner_fv is not None:
                    winner_name = getattr(winner_fv.current_fighter, "name", None) or getattr(winner_fv, "name", None)

                title_text = f"{winner_name} wins!" if winner_name else "Battle Over"
                sub_text = "Well fought."

                # panel layout
                panel_w, panel_h = 520, 240
                panel_rect = pygame.Rect((w - panel_w) // 2, (h - panel_h) // 2, panel_w, panel_h)
                panel = UIPanel(relative_rect=panel_rect, manager=self.ui)
                self.ui_elements.append(panel)

                # left: portrait (if available)
                portrait_rect = pygame.Rect(20, 28, 140, 140)
                if winner_fv is not None:
                    # try several sprite fields
                    sprite_path = None
                    if getattr(winner_fv, "current_fighter", None):
                        sprite_path = getattr(winner_fv.current_fighter, "fighter_selection_sprite", None) or getattr(winner_fv.current_fighter, "fighter_sprite", None)
                    else:
                        sprite_path = getattr(winner_fv, "fighter_selection_sprite", None) or getattr(winner_fv, "fighter_sprite", None)
                    portrait_surf = self.engine._load_image(sprite_path, size=(portrait_rect.w, portrait_rect.h))
                else:
                    portrait_surf = pygame.Surface((portrait_rect.w, portrait_rect.h), pygame.SRCALPHA)
                    portrait_surf.fill((30, 30, 30))

                portrait = UIImage(relative_rect=portrait_rect, image_surface=portrait_surf, manager=self.ui, container=panel)
                self.ui_elements.append(portrait)

                # title surface (bright, with shadow)
                title_w = panel_w - portrait_rect.right - 40
                title_h = 64
                title_surf = pygame.Surface((title_w, title_h), pygame.SRCALPHA)
                # shadow + main text
                title_shadow = self._popup_title_font.render(title_text, True, (0, 0, 0))
                title_main = self._popup_title_font.render(title_text, True, (255, 220, 120))
                title_surf.blit(title_shadow, (3, 3))
                title_surf.blit(title_main, (0, 0))
                title_rect = pygame.Rect(portrait_rect.right + 20, 32, title_w, title_h)
                title_img = UIImage(relative_rect=title_rect, image_surface=title_surf, manager=self.ui, container=panel)
                self.ui_elements.append(title_img)

                # subtitle (render onto a surface matching the rect to avoid scaling/stretching)
                sub_rect = pygame.Rect(portrait_rect.right - 60, title_rect.bottom + 8, title_w, 28)
                # create a surface exactly the size of the rect and center the rendered text on it
                sub_surf = pygame.Surface((sub_rect.width, sub_rect.height), pygame.SRCALPHA)
                text_surf = self._popup_sub_font.render(sub_text, True, (230, 230, 230))
                tx = (sub_rect.width - text_surf.get_width()) // 2
                ty = (sub_rect.height - text_surf.get_height()) // 2
                sub_surf.blit(text_surf, (tx, ty))
                sub_img = UIImage(relative_rect=sub_rect, image_surface=sub_surf, manager=self.ui, container=panel)
                self.ui_elements.append(sub_img)

                # Go back button (centered)
                btn_w, btn_h = 160, 48
                btn_x = (panel_w - btn_w) // 2
                btn_y = panel_h - btn_h - 18
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                go_btn = UIButton(relative_rect=btn_rect, text="Go back", manager=self.ui, container=panel)
                self.ui_elements.append(go_btn)

                # store refs for handling and cleanup
                self._win_panel = panel
                self._win_label = title_img
                self._win_button = go_btn

        if self.battle_engine.battle.is_battle_over:
            self.battle_over = True

    def request_go_back(self):
        # show confirmation popup if not already present
        if getattr(self, "_confirm_panel", None) is not None:
            return

        w, h = self.engine.window_size
        panel_w, panel_h = 420, 160
        panel_rect = pygame.Rect((w - panel_w) // 2, (h - panel_h) // 2, panel_w, panel_h)
        panel = UIPanel(relative_rect=panel_rect, manager=self.ui)
        self.ui_elements.append(panel)

        # message
        msg = "Quit match? Unsaved progress will be lost."
        font = pygame.font.SysFont(None, 20, bold=True)
        msg_surf = font.render(msg, True, (230, 230, 230))
        msg_rect = pygame.Rect(20, 20, panel_w - 40, 48)
        msg_img = UIImage(relative_rect=msg_rect, image_surface=pygame.Surface((msg_rect.width, msg_rect.height), pygame.SRCALPHA), manager=self.ui, container=panel)
        # blit text properly onto the surface to avoid scaling
        tmp_surf = pygame.Surface((msg_rect.width, msg_rect.height), pygame.SRCALPHA)
        tx = (msg_rect.width - msg_surf.get_width()) // 2
        ty = (msg_rect.height - msg_surf.get_height()) // 2
        tmp_surf.blit(msg_surf, (tx, ty))
        msg_img.set_image(tmp_surf)
        self.ui_elements.append(msg_img)

        # Yes / No buttons
        btn_w, btn_h = 120, 44
        yes_rect = pygame.Rect(panel_w // 2 - btn_w - 10, panel_h - btn_h - 14, btn_w, btn_h)
        no_rect = pygame.Rect(panel_w // 2 + 10, panel_h - btn_h - 14, btn_w, btn_h)

        yes_btn = UIButton(relative_rect=yes_rect, text="Yes", manager=self.ui, container=panel)
        no_btn = UIButton(relative_rect=no_rect, text="No", manager=self.ui, container=panel)

        self.ui_elements.extend([yes_btn, no_btn])

        self._confirm_panel = panel
        self._confirm_yes = yes_btn
        self._confirm_no = no_btn

    def _clear_confirm(self):
        # helper to remove confirmation popup
        if getattr(self, "_confirm_yes", None) is not None:
            try:
                self._confirm_yes.kill()
            except Exception:
                pass
            self._confirm_yes = None
        if getattr(self, "_confirm_no", None) is not None:
            try:
                self._confirm_no.kill()
            except Exception:
                pass
            self._confirm_no = None
        if getattr(self, "_confirm_panel", None) is not None:
            try:
                self._confirm_panel.kill()
            except Exception:
                pass
            self._confirm_panel = None
        # also remove from ui_elements if present
        try:
            self.ui_elements = [e for e in self.ui_elements if e not in (self._confirm_panel, self._confirm_yes, self._confirm_no)]
        except Exception:
            pass

    def process_event(self, event):
        # handle confirmation buttons first
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if getattr(self, "_confirm_yes", None) is not None and event.ui_element is self._confirm_yes:
                # confirm quit: navigate back via engine
                # clean up panel then go back
                self._clear_confirm()
                self.engine.go_back()
                return
            if getattr(self, "_confirm_no", None) is not None and event.ui_element is self._confirm_no:
                # cancel
                self._clear_confirm()
                return

        # If battle is over, allow popup input (Enter or Go back button),
        # but do not process targeting/move input.
        if self.battle_over:
            # Enter/Space to return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                from .title import TitleScreen
                self.engine.set_screen(TitleScreen)
                return

            # Allow clicking the Go back button
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if getattr(self, "_win_button", None) is not None and event.ui_element is self._win_button:
                    from .title import TitleScreen
                    self.engine.set_screen(TitleScreen)
                    return

            # ignore any other input when battle is over
            return

        if self.controller.target_mode:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.controller.target_index += 1

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.controller.target_index -= 1

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    target = self.controller.current_target()
                    if target:
                        self.controller.confirm_target(target)

                elif event.key == pygame.K_ESCAPE:
                    self.controller.target_mode = False
                    self.controller.pending_move = None
                    self.controller.pending_user = None

            if event.type == pygame.MOUSEMOTION:
                fid = self.renderer.get_fighter_at_pos(event.pos)
                if fid:
                    targets = self.controller.get_targets()
                    for idx, fv in enumerate(targets):
                        if id(fv) == fid:
                            self.controller.target_index = idx
                            break

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    fid = self.renderer.get_fighter_at_pos(event.pos)
                    if fid:
                        targets = self.controller.get_targets()
                        for fv in targets:
                            if id(fv) == fid:
                                self.controller.confirm_target(fv)
                                break

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.move_buttons:
                self.controller.start_targeting(event.ui_element.move_idx)

            # handle Go back button from win popup
            if getattr(self, "_win_button", None) is not None and event.ui_element is self._win_button:
                from .title import TitleScreen
                self.engine.set_screen(TitleScreen)
                return

        # allow selecting move by hovering when not in target mode
        if event.type == pygame.MOUSEMOTION and not self.controller.target_mode:
            mouse_pos = event.pos
            for btn in getattr(self, "move_buttons", []):
                # prefer absolute rect provided by pygame_gui; fall back to stored relative rect
                try:
                    rect = btn.get_absolute_rect()
                except Exception:
                    try:
                        # attempt to translate relative to container if available
                        if hasattr(self, "action_bar") and hasattr(self.action_bar, "relative_rect"):
                            rect = btn.relative_rect.move(self.action_bar.relative_rect.topleft)
                        else:
                            rect = btn.relative_rect
                    except Exception:
                        rect = btn.relative_rect

                if rect.collidepoint(mouse_pos):
                    try:
                        self.selected_move_idx = getattr(btn, "move_idx", 0)
                    except Exception:
                        self.selected_move_idx = 0
                    break

        # allow Enter/Space to close popup as well
        if self.battle_over and getattr(self, "_win_panel", None) is not None:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                from .title import TitleScreen
                self.engine.set_screen(TitleScreen)
                return

    def draw(self, surface):
        self.renderer.draw(surface, self.controller)

    def _build_buffs_and_statuses_ui(self, fv, center_x, y):
        # initialize caches
        if not hasattr(self, "_status_icons"):
            self._status_icons = {}
        if not hasattr(self, "_status_effects"):
            self._status_effects = {}

        # compute current effects list and a stable key for comparison
        effects = fv.current_buffs + fv.current_status
        def _effect_key(effect):
            if hasattr(effect, "stat"):
                return ("stat", getattr(effect, "stat", None), getattr(effect, "amount", None), getattr(effect, "duration", None))
            else:
                return ("status", getattr(effect, "id", None), getattr(effect, "stacks", 1), getattr(effect, "duration", None))

        current_key = tuple(_effect_key(e) for e in effects)

        # if nothing changed for this fighter, avoid rebuilding icons
        if self._status_effects.get(id(fv)) == current_key:
            return

        # Clear old icons for this fighter
        for el in self._status_icons.get(id(fv), []):
            try:
                el.kill()
            except Exception:
                pass

        self._status_icons[id(fv)] = []
        self._status_effects[id(fv)] = current_key

        if not effects:
            return

        icon_size = 48
        padding = 8

        total_width = len(effects) * icon_size + (len(effects) - 1) * padding
        start_x = int(center_x - total_width // 2)

        for i, effect in enumerate(effects):
            icon_path = (
                f"buff/{effect.stat}.svg"
                if hasattr(effect, "stat")
                else f"status/{effect.id}.svg"
            )

            surface = self.engine._load_icon(icon_path, size=(icon_size, icon_size))

            # create a working copy so we can draw duration text on top
            try:
                icon_surf = surface.copy()
            except Exception:
                icon_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_surf.blit(surface, (0, 0))

            # draw remaining-turns/duration if available (duration != -1)
            duration = None
            if hasattr(effect, "duration"):
                duration = getattr(effect, "duration", None)
            # some status types may use other naming; keep check flexible
            if duration is not None and duration != -1:
                txt = str(duration)
                # main text and outline text
                main = self._status_font.render(txt, True, (255, 230, 120))
                outline = self._status_font.render(txt, True, (0, 0, 0))

                tw, th = main.get_size()
                # center on the icon
                tx = (icon_surf.get_width() - tw) // 2
                ty = (icon_surf.get_height() - th) // 2

                # draw outline by blitting the black text with offsets around the center
                for ox, oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    icon_surf.blit(outline, (tx + ox, ty + oy))
                # main text on top
                icon_surf.blit(main, (tx, ty))

            rect = pygame.Rect(
                start_x + i * (icon_size + padding),
                y,
                icon_size,
                icon_size
            )

            img = UIImage(
                relative_rect=rect,
                image_surface=icon_surf,
                manager=self.ui
            )

            # Tooltip
            if hasattr(effect, "stat"):
                tooltip = f"{effect.stat} {effect.amount:+}"
                if effect.duration != -1:
                    tooltip += f"\nTurns: {effect.duration}"
            else:
                tooltip = effect.id
                if getattr(effect, "stacks", 1) > 1:
                    tooltip += f" x{effect.stacks}"
                if getattr(effect, "duration", -1) != -1:
                    tooltip += f"\nTurns: {effect.duration}"

            # set tooltip text (use method compatible with UIImage)
            try:
                img.set_tooltip(tooltip)
            except Exception:
                try:
                    img.tool_tip_text = tooltip
                except Exception:
                    pass

            self._status_icons[id(fv)].append(img)
            self.ui_elements.append(img)
    
    def _update_fighter_name_ui(self, fv, center_x, top_y):
        # render a larger, brighter name surface with glow/background and present it as a UIImage
        rect = pygame.Rect(center_x - 160, top_y - 100, 320, 48)

        name = fv.current_fighter.name.title()
        battle = self.battle_engine.battle
        is_active = fv is battle.current_context.active_fighter

        # pick base color from theme but brighten it for visibility
        try:
            base_col = self.theme.colour("active_text") if is_active else self.theme.colour("normal_text")
        except Exception:
            base_col = (255, 240, 200) if is_active else (220, 220, 220)

        base = pygame.Color(*base_col) if isinstance(base_col, (list, tuple)) else pygame.Color(base_col)
        # brighten
        text_col = pygame.Color(min(255, base.r + 80), min(255, base.g + 80), min(255, base.b + 80))

        # create surface and draw glow/background
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        # faint glow: blurred-ish by semi-transparent rounded rect slightly bigger
        glow = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (text_col.r, text_col.g, text_col.b, 28), glow.get_rect(), border_radius=12)
        surf.blit(glow, (-4, -4))

        # dark translucent panel for contrast
        pygame.draw.rect(surf, (8, 8, 8, 200), surf.get_rect(), border_radius=10)
        # thin bright border
        pygame.draw.rect(surf, (min(255, text_col.r + 30), min(255, text_col.g + 30), min(255, text_col.b + 30)), surf.get_rect(), width=2, border_radius=10)

        # render shadow + main text
        shadow = self._fighter_name_font.render(name, True, (0, 0, 0))
        main = self._fighter_name_font.render(name, True, text_col)

        tw, th = main.get_size()
        tx = (rect.width - tw) // 2
        ty = (rect.height - th) // 2

        surf.blit(shadow, (tx + 2, ty + 2))
        surf.blit(main, (tx, ty))

        # create or update UIImage
        img = self.fighter_name_labels.get(id(fv))
        if img is None:
            ui_img = UIImage(
                relative_rect=rect,
                image_surface=surf,
                manager=self.ui
            )
            self.fighter_name_labels[id(fv)] = ui_img
            self.ui_elements.append(ui_img)
        else:
            try:
                img.set_image(surf)
                img.set_relative_position(rect.topleft)
            except Exception:
                try:
                    img.image_surface = surf
                    img.set_relative_position(rect.topleft)
                except Exception:
                    try:
                        img.kill()
                    except Exception:
                        pass
                    ui_img = UIImage(
                        relative_rect=rect,
                        image_surface=surf,
                        manager=self.ui
                    )
                    self.fighter_name_labels[id(fv)] = ui_img
                    self.ui_elements.append(ui_img)

class BattleRenderer:
    def __init__(self, engine, battle_engine):
        self.engine = engine
        self.battle_engine = battle_engine
        self.views = {}
        self.fighter_anchors = {}
        self.fighter_rects = {}
        self.bg = pygame.Surface((1, 1))

    def load_assets(self):
        battle = self.battle_engine.battle
        # load full-size background first
        raw_bg = self.engine._load_image(
            battle.background_sprite,
            size=self.engine.window_size
        )

        # crop/raise the image by blitting it shifted up so the top is removed
        # configurable fraction (0.0..1.0) via config; default to 0.15 (15% of height)
        crop_frac = getattr(self.engine.config.options, "background_crop_top_fraction", 0.15)
        try:
            crop_frac = float(crop_frac)
        except Exception:
            crop_frac = 0.15
        crop_frac = max(0.0, min(0.9, crop_frac))

        h = self.engine.window_size[1]
        crop_y = int(h * crop_frac)

        bg = pygame.Surface(self.engine.window_size, pygame.SRCALPHA)
        # blit raw background shifted up by crop_y; this effectively crops the top
        bg.blit(raw_bg, (0, -crop_y))

        self.bg = bg

        self.views.clear()
        for side_idx, side in enumerate(battle.current_context.sides):
            for fv in side:
                self.views[id(fv)] = self.build_view(
                    fv, flip=bool(side_idx)
                )

    def draw(self, surface, controller):
        ctx = self.battle_engine.battle.current_context
        surface.blit(self.bg, (0, 0))

        left, right = ctx.sides[0][0], ctx.sides[1][0]

        # compute frames/rects and anchors for each fighter without blitting
        w, h = self.engine.window_size
        positions = [
            (left, (self.engine.window_size[0] * 0.25, self.engine.window_size[1] * 0.42)),
            (right, (self.engine.window_size[0] * 0.75, self.engine.window_size[1] * 0.42))
        ]

        # prepare rects/anchors and update UI (names/icons)
        for fv, pos in positions:
            view = self.views.get(id(fv))
            if not view:
                continue
            state = view["state"]
            frames = view[state]
            if not frames:
                continue
            frame = frames[view["frame"] % len(frames)]
            rect = frame.get_rect(center=pos)

            # store rect and anchor for later use (and for target highlight)
            self.fighter_rects[id(fv)] = rect
            ground_x = rect.centerx
            ground_y = rect.bottom - 18
            self.fighter_anchors[id(fv)] = (ground_x, ground_y)

            # update UI elements (names/status icons) now that rect is known
            screen = self.engine.active_screen
            name_y = rect.top - 40
            screen._update_fighter_name_ui(fv, rect.centerx, name_y)
            buffs_y = name_y
            screen._build_buffs_and_statuses_ui(fv, rect.centerx, buffs_y)

        # draw target highlight under fighters (uses anchors)
        if controller.target_mode:
            self._draw_target_highlight(controller)

        # now blit fighter frames so they appear above the ring
        for fv, pos in positions:
            view = self.views.get(id(fv))
            if not view:
                continue
            state = view["state"]
            frames = view[state]
            if not frames:
                continue
            frame = frames[view["frame"] % len(frames)]
            rect = self.fighter_rects.get(id(fv))
            if rect:
                surface.blit(frame, rect)

        # draw bars (kept after fighters)
        self._draw_hp(left, 110, 100)
        self._draw_shield(left, 110, 100)
        self._draw_charge(left, 110, 120)

        right_x = self.engine.window_size[0] - 430
        self._draw_hp(right, right_x, 100)
        self._draw_shield(right, right_x, 100)
        self._draw_charge(right, right_x, 120)

        if controller.target_mode:
            # target highlight already drawn under fighters; nothing further to do
            pass

    def build_view(self, fv, flip=False):
        # load original image (no forced scaling) and scale it to fit within a max box while preserving aspect ratio
        max_w, max_h = 250, 250
        # request original image by not passing size
        orig = self.engine._load_image(fv.current_fighter.fighter_sprite, size=None, flip=False)

        base = orig
        try:
            iw, ih = orig.get_size()
        except Exception:
            iw, ih = 0, 0

        # if we have a valid image size, compute scale preserving aspect ratio
        if iw > 0 and ih > 0:
            scale = min(max_w / iw, max_h / ih, 1.0)
            new_w = max(1, int(round(iw * scale)))
            new_h = max(1, int(round(ih * scale)))
            try:
                if flip:
                    # flip original then scale
                    tmp = pygame.transform.flip(orig, True, False)
                else:
                    tmp = orig
                base = pygame.transform.smoothscale(tmp, (new_w, new_h))
            except Exception:
                # fallback: ask engine to provide a sized image (best-effort)
                base = self.engine._load_image(fv.current_fighter.fighter_sprite, size=(max_w, max_h), flip=flip)
        else:
            # fallback: force a sized image if original couldn't be loaded properly
            base = self.engine._load_image(fv.current_fighter.fighter_sprite, size=(max_w, max_h), flip=flip)

        return {
            "idle": self._load_anim(fv, "idle", 2, base, flip),
            "attack": self._load_anim(fv, "attack", 3, base, flip),

            "state": "idle",
            "frame": 0,
            "timer": 0.0,

            "attack_move": None,
            "played_sounds": set(),
        }
    
    def _draw_fighter(self, fv, pos):
        view = self.views.get(id(fv))
        if not view:
            return

        state = view["state"]
        frames = view[state]
        frame = frames[view["frame"] % len(frames)]

        rect = frame.get_rect(center=pos)
        self.engine.screen.blit(frame, rect)

        self.fighter_rects[id(fv)] = rect

        ground_x = rect.centerx
        ground_y = rect.bottom - 18
        self.fighter_anchors[id(fv)] = (ground_x, ground_y)

        screen = self.engine.active_screen

        name_y = rect.top - 40
        screen._update_fighter_name_ui(fv, rect.centerx, name_y)

        buffs_y = name_y + 30 + 8
        screen._build_buffs_and_statuses_ui(fv, rect.centerx, buffs_y)
    
    def _load_anim(self, fv, key: str, frames_needed: int, base, flip=False):
        anim_paths = fv.current_fighter.animations.get(key, [])

        frames = [
            self.engine._load_image(
                path,
                size=base.get_size(),
                flip=flip
            )
            for path in anim_paths
        ]

        # fallback: reuse base frame
        if not frames:
            frames = [base] * frames_needed

        return frames
    
    def _bar(self, surface, x, y, w, h, val, max_val, fg_key, bg_key):
        theme = self.engine.theme

        fg = theme.colour(fg_key)
        bg = theme.colour(bg_key)

        pygame.draw.rect(surface, bg, (x, y, w, h))
        ratio = 0 if max_val <= 0 else min(1.0, val / max_val)
        pygame.draw.rect(surface, fg, (x, y, int(w * ratio), h))

    def _draw_hp(self, fv, x, y, w=320, h=22):
        self._bar(
            self.engine.screen,
            x, y, w, h,
            fv.current_stats.hp,
            fv.computed_stats.hp,
            "hp_bar",
            "bar_bg"
        )

    def _draw_charge(self, fv, x, y, w=320, h=12):
        self._bar(
            self.engine.screen,
            x, y, w, h,
            fv.current_stats.charge,
            fv.computed_stats.charge,
            "charge_bar",
            "bar_bg"
        )

    def _overlay_bar(self, x, y, w, h, ratio, color_key):
        theme = self.engine.theme
        pygame.draw.rect(
            self.engine.screen,
            theme.colour(color_key),
            (x, y, int(w * ratio), h)
        )

    def _draw_shield(self, fv, x, y, w=320, h=22):
        if fv.current_stats.shield <= 0:
            return

        ratio = fv.current_stats.shield / max(1, fv.computed_stats.shield)
        self._overlay_bar(x, y, w, h // 3, ratio, "shield_bar")

    def _draw_target_highlight(self, controller):
        ctx = self.battle_engine.battle.current_context

        user = controller.pending_user
        if not user:
            return

        # determine valid targets
        if user in ctx.sides[0]:
            targets = ctx.sides[1]
        else:
            targets = ctx.sides[0]

        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 3.0) + 1) / 2

        base_radius = 80
        radius = base_radius + pulse * 6

        # base shape size
        width = int(radius * 2.2)
        height = int(radius * 0.55)
        alpha = int(110 + pulse * 70)

        # stroke thickness scales with pulse for a more "pulsing" ring
        stroke_width = max(5, int(5 + pulse * 6))

        # add padding so the stroke isn't clipped
        pad = stroke_width + 2
        ring = pygame.Surface((width + pad * 2, height + pad * 2), pygame.SRCALPHA)
        ring_color = self.engine.theme.colour("target_ring")

        if len(ring_color) == 4:
            r, g, b, _ = ring_color
        else:
            r, g, b = ring_color

        pygame.draw.ellipse(
            ring,
            (r, g, b, alpha),
            ring.get_rect(),
            width=stroke_width
        )

        target = controller.current_target()
        if not target:
            return

        anchor = self.fighter_anchors.get(id(target))
        if not anchor:
            return

        # nudge the highlight upward so it appears slightly above the ground anchor
        # use a fraction of the radius so the offset scales with ring size
        vertical_nudge = int(radius * -0.1)
        nudged_anchor = (anchor[0], anchor[1] - vertical_nudge)
        rect = ring.get_rect(center=nudged_anchor)

        self.engine.screen.blit(ring, rect)

    def get_fighter_at_pos(self, pos):
        for fid, rect in reversed(list(self.fighter_rects.items())):
            if rect.collidepoint(pos):
                return fid
        return None
    
    def set_attack(self, fv, move):
        view = self.views.get(id(fv))
        if not view:
            return

        view["state"] = "attack"
        view["frame"] = 0
        view["timer"] = 0.0

        view["attack_move"] = move
        view["played_sounds"].clear()

    def update(self, dt):
        audio = self.engine.registry.get("audio")

        for view in self.views.values():
            state = view["state"]
            frames = view[state]
            if not frames:
                continue

            view["timer"] += dt
            frame_time = 0.18 if state == "idle" else 0.12

            while view["timer"] >= frame_time:
                view["timer"] -= frame_time
                view["frame"] += 1

                # 🔊 sound sync (move-owned)
                if state == "attack":
                    move = view.get("attack_move")
                    frame_idx = view["frame"]

                    # play once on impact frame (example: frame 1)
                    if (
                        move
                        and move.sound
                        and frame_idx == 1
                        and frame_idx not in view["played_sounds"]
                    ):
                        audio.play_path(move.sound)
                        view["played_sounds"].add(frame_idx)

                # attack animation ends
                if state == "attack" and view["frame"] >= len(frames):
                    view["state"] = "idle"
                    view["frame"] = 0
                    view["timer"] = 0.0
                    view["attack_move"] = None
                    view["played_sounds"].clear()
                    break

class BattleController:
    def __init__(self, engine, battle_engine):
        self.engine = engine
        self.battle_engine = battle_engine

        self.target_mode = False
        self.pending_move = None
        self.pending_user = None

        self.log_lines = []
        self.pending_logs = []
        self.log_timer = 0.0
        self.log_interval = 0.7

        self.target_index = 0
        # mark when we've handled end-of-battle logs
        self.battle_ended = False

    def current_moves(self, fv):
        move_engine = self.engine.registry.get("moves")
        return [
            move_engine.set[m]
            for m in fv.current_fighter.moves
            if m in move_engine.set
        ][:4]

    def start_targeting(self, idx):
        ctx = self.battle_engine.battle.current_context
        user = ctx.active_fighter
        moves = self.current_moves(user)

        if idx >= len(moves):
            return

        move = moves[idx]
        if user.current_stats.charge < move.charge_usage:
            ctx.log_stack.append(f"{user.current_fighter.name} lacks charge.")
            return

        # Immediately display any queued logs (and any new logs from context)
        # so the log box "snaps" to the current move instead of waiting.
        # Pull any waiting logs from the context first.
        new_logs = ctx.get_next_logs()
        if new_logs:
            self.log_lines.extend(new_logs)

        # Flush pending_logs into visible lines immediately
        if self.pending_logs:
            self.log_lines.extend(self.pending_logs)
            self.pending_logs.clear()

        # ensure immediate display
        self.log_timer = 0.0

        self.pending_move = move
        self.pending_user = user
        self.target_mode = True
        self.target_index = 0

    def confirm_target(self, target):
        screen = self.engine.active_screen
        screen.renderer.set_attack(self.pending_user, self.pending_move)

        self.battle_engine.step((self.pending_move.id, target))

        self.pending_move = None
        self.pending_user = None
        self.target_mode = False

    def get_targets(self):
        ctx = self.battle_engine.battle.current_context
        user = self.pending_user

        if not user:
            return []

        # enemy side
        if user in ctx.sides[0]:
            enemies = ctx.sides[1]
        else:
            enemies = ctx.sides[0]

        # allow self-targeting
        return enemies + [user]

    def current_target(self):
        targets = self.get_targets()
        if not targets:
            return None
        return targets[self.target_index % len(targets)]


    def update_logs(self, dt):
        ctx = self.battle_engine.battle.current_context

        # If battle has ended, flush remaining logs once and stop pulling new ones.
        if self.battle_engine.battle.is_battle_over:
            if not self.battle_ended:
                # grab any remaining logs from context
                new_logs = ctx.get_next_logs()
                if new_logs:
                    self.pending_logs.extend(new_logs)
                # flush everything into visible lines immediately
                if self.pending_logs:
                    self.log_lines.extend(self.pending_logs)
                    self.pending_logs.clear()
                self.battle_ended = True
            return

        # normal behavior while battle is ongoing
        new_logs = ctx.get_next_logs()
        if new_logs:
            self.pending_logs.extend(new_logs)

        self.log_timer -= dt
        if self.log_timer <= 0 and self.pending_logs:
            self.log_lines.append(self.pending_logs.pop(0))
            self.log_timer = self.log_interval

    def visible_logs(self):
        return self.log_lines[-6:]