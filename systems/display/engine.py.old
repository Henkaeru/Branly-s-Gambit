import os
import pygame
from typing import Dict, List
from systems.battle.engine import BattleMode
from systems.battle.schema import Battle
from systems.moves.schema import Move

class DisplayEngine:
    def __init__(self, display_config, registry):
        self.config = display_config
        self.registry = registry
        self.battle_engine = registry.get("battle")
        self.options = self.config.options.model_copy(deep=True)
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self._apply_options()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.state_stack = ["title"]
        self.menu_index = 0
        self.option_index = 0
        self.log_lines: List[str] = []
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self.title_image = self._load_image(self.options.title_image, size=(self.width, self.height))
        self._init_char_select()
        self._battle_reset()
        self.char_phase = 0  # 0: P1 picking, 1: P2 picking
        self.p1_pick = None
        self.p2_pick = None
        self.pending_logs: List[str] = []
        self.log_timer = 0.0
        self.log_interval = 0.7
        self.target_mode = False
        self.target_idx = 0
        self.pending_move = None
        self.pending_user = None

    # --- window/options ---
    def _apply_options(self):
        flags = pygame.FULLSCREEN if self.options.fullscreen else 0
        self.width, self.height = self.options.width, self.options.height
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("Branly's Gambit")
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.options.master_volume)

    # --- util ---
    def _fv_key(self, fv) -> int: return id(fv)

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

    def _load_icon(self, path: str, size=(32, 32)) -> pygame.Surface:
        """Load an icon from the given path and resize it."""
        full_path = f"assets/textures/{path}"
        if os.path.exists(full_path):
            try:
                img = pygame.image.load(full_path).convert_alpha()
                return pygame.transform.smoothscale(img, size)
            except pygame.error:
                pass
        # Fallback to a blank surface if the icon cannot be loaded
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))  # Transparent
        return surf

    # --- title screen ---
    def _draw_title(self):
        self.screen.blit(self.title_image, (0, 0))
        items = ["Play", "Options", "Quit"]
        button_width, button_height = 200, 50
        button_spacing = 20
        start_y = self.height // 2 - (len(items) * (button_height + button_spacing)) // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, txt in enumerate(items):
            x = self.width // 2 - button_width // 2
            y = start_y + i * (button_height + button_spacing)
            rect = pygame.Rect(x, y, button_width, button_height)
            is_selected = i == self.menu_index or rect.collidepoint(mouse_x, mouse_y)

            # Draw button background
            bg_color = (80, 80, 80) if is_selected else (50, 50, 50)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)

            # Draw button border if selected
            if is_selected:
                pygame.draw.rect(self.screen, (230, 200, 80), rect, 3, border_radius=8)

            # Render and draw text
            color = (255, 255, 255)
            surf = self.font.render(txt, True, color)
            self.screen.blit(surf, (x + button_width // 2 - surf.get_width() // 2, y + button_height // 2 - surf.get_height() // 2))

        pygame.display.flip()

    def _handle_title_event(self, e):
        items = ["Play", "Options", "Quit"]
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_width, button_height = 200, 50
        button_spacing = 20
        start_y = self.height // 2 - (len(items) * (button_height + button_spacing)) // 2

        if e.type == pygame.MOUSEMOTION:
            for i in range(len(items)):
                x = self.width // 2 - button_width // 2
                y = start_y + i * (button_height + button_spacing)
                rect = pygame.Rect(x, y, button_width, button_height)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.menu_index = i

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:  # Left mouse button
            x = self.width // 2 - button_width // 2
            y = start_y + self.menu_index * (button_height + button_spacing)
            rect = pygame.Rect(x, y, button_width, button_height)
            if rect.collidepoint(mouse_x, mouse_y):
                choice = items[self.menu_index]
                if choice == "Play":
                    self._push_state("char_select")
                elif choice == "Options":
                    self._push_state("options")
                elif choice == "Quit":
                    self._quit()

        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(items)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(items)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = items[self.menu_index]
                if choice == "Play":
                    self._push_state("char_select")
                elif choice == "Options":
                    self._push_state("options")
                elif choice == "Quit":
                    self._quit()
            elif e.key == pygame.K_ESCAPE:
                self._quit()

    # --- options screen ---
    def _options_list(self):
        return [
            ("Fullscreen", lambda: str(self.options.fullscreen)),
            ("Master Volume", lambda: f"{self.options.master_volume:.1f}"),
            ("Resolution", lambda: f"{self.options.width}x{self.options.height}"),
        ]

    def _apply_option_change(self, idx, delta):
        if idx == 0:
            self.options.fullscreen = not self.options.fullscreen
        elif idx == 1:
            self.options.master_volume = max(0.0, min(1.0, self.options.master_volume + delta * 0.1))
        elif idx == 2:
            self.options.width = max(640, self.options.width + delta * 160)
            self.options.height = max(480, self.options.height + delta * 90)
        self._apply_options()

    def _draw_options(self):
        self.screen.fill((15, 15, 15))  # Dark background for the options screen

        # Draw a centered panel for the options
        panel_width, panel_height = 400, 300
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        pygame.draw.rect(self.screen, (30, 30, 30), (panel_x, panel_y, panel_width, panel_height), border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=12)

        # Draw the header
        header = self.font.render("Options", True, (255, 255, 255))
        self.screen.blit(header, (self.width // 2 - header.get_width() // 2, panel_y + 20))

        # Draw each option
        options = self._options_list()
        option_spacing = 50
        start_y = panel_y + 80
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, (name, val_fn) in enumerate(options):
            option_x = panel_x + 20
            option_y = start_y + i * option_spacing
            rect = pygame.Rect(option_x, option_y, panel_width - 40, 40)
            is_selected = i == self.option_index or rect.collidepoint(mouse_x, mouse_y)

            # Highlight the selected option
            color = (230, 200, 80) if is_selected else (220, 220, 220)
            bg_color = (50, 50, 50) if is_selected else (30, 30, 30)

            # Draw background for the option
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
            if is_selected:
                pygame.draw.rect(self.screen, (230, 200, 80), rect, 2, border_radius=8)

            # Render and draw the option text
            option_text = self.font.render(f"{name}: {val_fn()}", True, color)
            self.screen.blit(option_text, (option_x + 20, option_y + 10))

        # Draw the hint at the bottom
        hint = self.small_font.render("Arrows/Mouse: navigate  Enter/Space/Click: toggle  ESC: back", True, (180, 180, 180))
        self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, panel_y + panel_height - 40))

        pygame.display.flip()

    def _handle_options_event(self, e):
        options = self._options_list()
        panel_width, panel_height = 400, 300
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        option_spacing = 50
        start_y = panel_y + 80
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if e.type == pygame.MOUSEMOTION:
            for i in range(len(options)):
                option_x = panel_x + 20
                option_y = start_y + i * option_spacing
                rect = pygame.Rect(option_x, option_y, panel_width - 40, 40)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.option_index = i

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:  # Left mouse button
            option_x = panel_x + 20
            option_y = start_y + self.option_index * option_spacing
            rect = pygame.Rect(option_x, option_y, panel_width - 40, 40)
            if rect.collidepoint(mouse_x, mouse_y):
                self._apply_option_change(self.option_index, 1 if self.option_index == 0 else 0)

        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.option_index = (self.option_index - 1) % len(options)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.option_index = (self.option_index + 1) % len(options)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self._apply_option_change(self.option_index, -1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self._apply_option_change(self.option_index, 1)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._apply_option_change(self.option_index, 1 if self.option_index == 0 else 0)
            elif e.key == pygame.K_ESCAPE:
                self._pop_state()

    # --- character select ---
    def _init_char_select(self):
        fighters = list(self.registry.get("fighters").set.values())
        self.fighter_list = fighters
        self.grid_cols = 6 if len(fighters) > 6 else max(1, len(fighters))
        self.grid_sel = 0
        self.char_phase = 0
        self.p1_pick = None
        self.p2_pick = None

    def _draw_char_select(self):
        self.screen.fill((15, 25, 35))
        title = self.font.render("Character Select", True, (255, 255, 255))
        self.screen.blit(title, (40, 30))
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if not self.fighter_list:
            warn = self.font.render("No fighters available.", True, (200, 80, 80))
            self.screen.blit(warn, (40, 100))
        else:
            cell_w, cell_h = 180, 200
            padding = 16
            for idx, fighter in enumerate(self.fighter_list):
                row = idx // self.grid_cols
                col = idx % self.grid_cols
                x = 40 + col * (cell_w + padding)
                y = 120 + row * (cell_h + padding)
                rect = pygame.Rect(x, y, cell_w, cell_h)
                sprite = self._load_image(fighter.fighter_selection_sprite, size=(cell_w, cell_h - 40))
                self.screen.blit(sprite, rect)
                name = self.small_font.render(fighter.name, True, (240, 240, 240))
                self.screen.blit(name, (x + 8, y + cell_h - 30))

                # Highlight borders
                border_color = None
                if self.p1_pick == idx:
                    border_color = (60, 140, 255)
                if self.p2_pick == idx:
                    border_color = (220, 60, 60)
                if border_color:
                    pygame.draw.rect(self.screen, border_color, rect.inflate(6, 6), 4)
                if idx == self.grid_sel or rect.collidepoint(mouse_x, mouse_y):
                    pygame.draw.rect(self.screen, (220, 200, 80), rect.inflate(10, 10), 3)

            phase_txt = "P1 select (Enter/Click)" if self.char_phase == 0 else "P2 select (Enter/Click)"
            phase = self.font.render(phase_txt, True, (255, 255, 255))
            self.screen.blit(phase, (40, 80))
            hint = self.small_font.render("Mouse: hover/select  Arrows/WASD: move  Enter/Space: pick  ESC: back", True, (180, 180, 180))
            self.screen.blit(hint, (40, self.height - 50))
        pygame.display.flip()

    def _handle_char_select_event(self, e):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cell_w, cell_h = 180, 200
        padding = 16

        if not self.fighter_list:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self._pop_state()
            return

        if e.type == pygame.MOUSEMOTION:
            for idx, fighter in enumerate(self.fighter_list):
                row = idx // self.grid_cols
                col = idx % self.grid_cols
                x = 40 + col * (cell_w + padding)
                y = 120 + row * (cell_h + padding)
                rect = pygame.Rect(x, y, cell_w, cell_h)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.grid_sel = idx

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:  # Left mouse button
            for idx, fighter in enumerate(self.fighter_list):
                row = idx // self.grid_cols
                col = idx % self.grid_cols
                x = 40 + col * (cell_w + padding)
                y = 120 + row * (cell_h + padding)
                rect = pygame.Rect(x, y, cell_w, cell_h)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.grid_sel = idx
                    if self.char_phase == 0:
                        self.p1_pick = self.grid_sel
                        self.char_phase = 1
                    else:
                        self.p2_pick = self.grid_sel
                        self._start_battle()

        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self.grid_sel = (self.grid_sel - 1) % len(self.fighter_list)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.grid_sel = (self.grid_sel + 1) % len(self.fighter_list)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.grid_sel = (self.grid_sel - self.grid_cols) % len(self.fighter_list)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.grid_sel = (self.grid_sel + self.grid_cols) % len(self.fighter_list)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.char_phase == 0:
                    self.p1_pick = self.grid_sel
                    self.char_phase = 1
                else:
                    self.p2_pick = self.grid_sel
                    self._start_battle()
            elif e.key == pygame.K_ESCAPE:
                self._pop_state()
                # Reset picks when leaving char select
                self._init_char_select()

    # --- battle setup ---
    def _battle_reset(self):
        self.views: Dict[int, dict] = {}
        self.bg = pygame.Surface((1, 1))
        self.battle_over = False
        self.exit_confirm = False
        self.log_lines.clear()
        # Reset char select picks when returning from battle
        self._init_char_select()

    def _load_battle_assets(self):
        battle = self.battle_engine.battle
        bg_path = battle.background_sprite
        self.bg = self._load_image(bg_path, size=(self.width, self.height))
        if battle.music or self.options.battle_music:
            music_path = battle.music or self.options.battle_music
            if music_path and os.path.exists(music_path):
                try:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(self.options.master_volume)
                    pygame.mixer.music.play(-1)
                except pygame.error:
                    pass
        self.views.clear()
        for side_idx, side in enumerate(battle.current_context.sides):
            for fv in side:
                self.views[self._fv_key(fv)] = self._build_view(fv, flip=bool(side_idx))

    def _build_view(self, fv, flip=False):
        base = self._load_image(fv.current_fighter.fighter_sprite, size=(260, 260), flip=flip)
        return {
            "idle": self._load_anim(fv, "idle", 2, base, flip),
            "attack": self._load_anim(fv, "attack", 3, base, flip),
            "state": "idle", "frame": 0, "timer": 0.0, "flip": flip,
        }

    def _load_anim(self, fv, key: str, frames_needed: int, base, flip=False):
        frames = [self._load_image(p, size=base.get_size(), flip=flip) for p in fv.current_fighter.animations.get(key, [])]
        if not frames:
            frames = [base] * frames_needed
        return frames

    def _start_battle(self):
        left = self.fighter_list[self.p1_pick or 0].id
        right = self.fighter_list[self.p2_pick or 0].id
        battle = Battle.from_sides(
            id="1v1_match",
            sides=[[left], [right]],
            background_sprite=self.options.battle_background,
            music=self.options.battle_music,
        )
        self.battle_engine.start(battle)
        self.battle_engine.set_battle_mode(BattleMode.LOCAL_1V1)
        self._battle_reset()
        self._load_battle_assets()
        self._push_state("battle")

    # --- state stack ---
    def _push_state(self, state):
        self.state_stack.append(state)
        if state == "battle":
            self.menu_index = 0
        if state == "char_select":
            self.exit_confirm = False

    def _pop_state(self):
        if len(self.state_stack) > 1:
            self.state_stack.pop()

    def _quit(self):
        pygame.quit()
        raise SystemExit

    # --- battle helpers (UI) ---
    def _bar(self, x, y, w, h, val, max_val, color, bg=(40, 40, 40)):
        pygame.draw.rect(self.screen, bg, (x, y, w, h))
        ratio = 0 if max_val <= 0 else max(0.0, min(1.0, val / max_val))
        pygame.draw.rect(self.screen, color, (x, y, w * ratio, h))

    def _draw_hp_shield(self, fv, x, y, w=320, h=22):
        self._bar(x, y, w, h, fv.current_stats.hp, fv.computed_stats.hp, (200, 60, 60))
        if fv.current_stats.shield > 0:
            shield_ratio = fv.current_stats.shield / max(1, fv.computed_stats.shield)
            pygame.draw.rect(self.screen, (70, 140, 220), (x, y, w * shield_ratio, h // 3))

    def _draw_charge(self, fv, x, y, w=320, h=12):
        self._bar(x, y, w, h, fv.current_stats.charge, fv.computed_stats.charge, (230, 200, 60))

    def _invert_icon_color(self, icon: pygame.Surface) -> pygame.Surface:
        """Invert the colors of the given icon."""
        inverted_icon = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
        width, height = icon.get_size()
        for x in range(width):
            for y in range(height):
                r, g, b, a = icon.get_at((x, y))
                inverted_icon.set_at((x, y), (255 - r, 255 - g, 255 - b, a))
        return inverted_icon

    def _draw_buffs_and_statuses(self, fv, center_x, y):
        """Draw buffs and statuses as icons with turn count and tooltips on hover."""
        icon_size = 32
        padding = 8
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Combine buffs and statuses into a single list for layout calculation
        buffs_and_statuses = fv.current_buffs + fv.current_status

        # Calculate total width of all icons (including padding)
        total_width = len(buffs_and_statuses) * icon_size + max(0, len(buffs_and_statuses) - 1) * padding

        # Calculate the starting x position to center the icons
        start_x = center_x - total_width // 2
        current_x = start_x

        # Draw buffs
        for buff in fv.current_buffs:
            icon = self._load_icon(f"buff/{buff.stat}.svg", size=(icon_size, icon_size))
            if buff.amount < 0:  # Check if it's a debuff
                icon = self._invert_icon_color(icon)
            rect = pygame.Rect(current_x, y, icon_size, icon_size)
            self.screen.blit(icon, (current_x, y))

            # Draw turn count inside the icon with a black border
            if buff.duration != -1:
                duration_text = str(buff.duration)
                duration_surf = self.small_font.render(duration_text, True, (255, 255, 255))
                duration_bg = self.small_font.render(duration_text, True, (0, 0, 0))
                duration_rect = duration_surf.get_rect(center=(current_x + icon_size // 2, y + icon_size // 2))
                self.screen.blit(duration_bg, duration_rect.move(1, 1))  # Black border
                self.screen.blit(duration_surf, duration_rect)

            # Show tooltip only if the mouse is hovering over the icon
            if rect.collidepoint(mouse_x, mouse_y):
                tooltip = f"{buff.stat} {'+' if buff.amount >= 0 else ''}{buff.amount}"
                self._draw_tooltip(tooltip, current_x, y + icon_size + 4)

            current_x += icon_size + padding

        # Draw statuses
        for status in fv.current_status:
            icon = self._load_icon(f"status/{status.id}.svg", size=(icon_size, icon_size))
            if getattr(status, "is_debuff", False):  # Check if it's a debuff
                icon = self._invert_icon_color(icon)
            rect = pygame.Rect(current_x, y, icon_size, icon_size)
            self.screen.blit(icon, (current_x, y))

            # Draw turn count inside the icon with a black border
            if getattr(status, "duration", -1) != -1:
                duration_text = str(status.duration)
                duration_surf = self.small_font.render(duration_text, True, (255, 255, 255))
                duration_bg = self.small_font.render(duration_text, True, (0, 0, 0))
                duration_rect = duration_surf.get_rect(center=(current_x + icon_size // 2, y + icon_size // 2))
                self.screen.blit(duration_bg, duration_rect.move(1, 1))  # Black border
                self.screen.blit(duration_surf, duration_rect)

            # Show tooltip only if the mouse is hovering over the icon
            if rect.collidepoint(mouse_x, mouse_y):
                tooltip = status.id
                if getattr(status, "stacks", 1) > 1:
                    tooltip += f" x{status.stacks}"
                tooltip += f" ({status.effect})" if hasattr(status, "effect") else ""
                self._draw_tooltip(tooltip, current_x, y + icon_size + 4)

            current_x += icon_size + padding

    def _draw_tooltip(self, text, x, y):
        """Draw a tooltip with the given text at the specified position."""
        font = self.small_font
        tooltip_surf = font.render(text, True, (255, 255, 255))
        tooltip_bg = pygame.Surface((tooltip_surf.get_width() + 8, tooltip_surf.get_height() + 4), pygame.SRCALPHA)
        tooltip_bg.fill((0, 0, 0, 180))  # Semi-transparent background
        self.screen.blit(tooltip_bg, (x, y))
        self.screen.blit(tooltip_surf, (x + 4, y + 2))

    def _draw_fighter(self, fv, pos):
        view = self.views[self._fv_key(fv)]
        frame = view[view["state"]][view["frame"] % len(view[view["state"]])]
        rect = frame.get_rect(center=pos)
        self.screen.blit(frame, rect)

        # Highlight active fighter name
        color = (60, 140, 255) if fv is self.battle_engine.battle.current_context.active_fighter else (255, 255, 255)
        name = self.font.render(fv.current_fighter.name, True, color)
        name_x = rect.centerx - name.get_width() // 2
        name_y = rect.top - 40
        self.screen.blit(name, (name_x, name_y))

        # Draw buffs and statuses centered under the name
        buffs_statuses_y = name_y + name.get_height() + 8
        self._draw_buffs_and_statuses(fv, rect.centerx, buffs_statuses_y)

    def _draw_moves(self, moves, user, selected):
        box_h = self.options.move_height
        box_y = self.height - box_h
        pygame.draw.rect(self.screen, (18, 18, 18), (0, box_y, self.width, box_h))
        for i, move in enumerate(moves):
            usable = user.current_stats.charge >= move.charge_usage
            color = (90, 90, 90) if not usable else (70, 110, 70)
            if i == selected:
                color = (160, 160, 80)
            x = 40 + i * 300
            y = box_y + 20
            pygame.draw.rect(self.screen, color, (x, y, 260, 60), border_radius=8)
            t1 = self.font.render(f"{i+1}. {move.name}", True, (0, 0, 0))
            t2 = self.small_font.render(f"Charge: {move.charge_usage}", True, (10, 10, 10))
            self.screen.blit(t1, (x + 12, y + 10))
            self.screen.blit(t2, (x + 12, y + 36))

    def _draw_log(self):
        box_h = self.options.log_height
        box_y = self.height - box_h - self.options.move_height
        pygame.draw.rect(self.screen, (25, 25, 25), (0, box_y, self.width, box_h))
        for i, line in enumerate(self.log_lines[-6:]):
            txt = self.small_font.render(line, True, (240, 240, 240))
            self.screen.blit(txt, (20, box_y + 10 + i * 20))

    # --- battle runtime ---
    def _current_moves(self, fv) -> List[Move]:
        move_engine = self.registry.get("moves")
        return [move_engine.set[m] for m in fv.current_fighter.moves if m in move_engine.set][:4]

    def _choose_target(self, user):
        ctx = self.battle_engine.battle.current_context
        opponent = 1 - ctx.active_side
        for fv in ctx.sides[opponent]:
            if fv.alive:
                return fv
        return None

    def _play_sound(self, move: Move | None):
        if not move or not move.sound or not os.path.exists(move.sound):
            return
        if move.sound not in self.sound_cache:
            try:
                self.sound_cache[move.sound] = pygame.mixer.Sound(move.sound)
            except pygame.error:
                return
        self.sound_cache[move.sound].play()

    # --- battle runtime helpers ---
    def _target_list(self, user):
        ctx = self.battle_engine.battle.current_context
        # Allow selecting self as target
        opponent = 1 - ctx.active_side
        targets = [fv for fv in ctx.sides[opponent] if fv.alive]
        # Add self if alive
        if user.alive:
            targets.append(user)
        return targets

    def _logs(self, dt):
        new_logs = self.battle_engine.battle.current_context.get_next_logs()
        if new_logs:
            self.pending_logs.extend(new_logs)
        self.log_timer -= dt
        if self.log_timer <= 0 and self.pending_logs:
            self.log_lines.append(self.pending_logs.pop(0))
            self.log_timer = self.log_interval

    def _start_targeting(self, idx: int):
        if self.pending_logs:
            return
        ctx = self.battle_engine.battle.current_context
        user = ctx.active_fighter
        moves = self._current_moves(user)
        if not moves:
            return
        idx = min(idx, len(moves) - 1)
        move = moves[idx]
        if user.current_stats.charge < move.charge_usage:
            ctx.log_stack.append(f"{user.current_fighter.name} lacks charge for {move.name}.")
            return
        targets = self._target_list(user)
        if not targets:
            return
        self.pending_move = move
        self.pending_user = user
        self.target_mode = True
        self.target_idx = 0

        # Precompute target rectangles using unique identifiers (e.g., id())
        self.target_rects = {id(target): self._get_target_rect(target) for target in targets}

    def _confirm_target(self):
        if not self.pending_move or not self.pending_user:
            self.target_mode = False
            return

        targets = self._target_list(self.pending_user)
        if not targets:
            self.target_mode = False
            return

        # Ensure the target index is valid
        target = targets[self.target_idx % len(targets)]
        if not target:
            self.target_mode = False
            return

        # Play the move sound and execute the move
        self._play_sound(self.pending_move)
        self._set_attack(self.pending_user)
        self.battle_engine.step((self.pending_move.id, target))

        # Reset targeting state
        self.pending_move = None
        self.pending_user = None
        self.target_mode = False
        self.target_idx = 0  # Reset target index

    def _handle_battle_event(self, e, selected_ref):
        if e.type == pygame.MOUSEMOTION or e.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()

        if self.battle_over:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._pop_state()
            return

        if self.exit_confirm:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_y, pygame.K_RETURN):
                    self._pop_state()
                elif e.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.exit_confirm = False
            return

        if self.pending_logs:
            return

        if self.target_mode:
            targets = self._target_list(self.pending_user or self.battle_engine.battle.current_context.active_fighter)

            if e.type == pygame.MOUSEMOTION:
                # Use precomputed rectangles for efficiency
                for idx, target in enumerate(targets):
                    rect = self.target_rects.get(id(target))
                    if rect and rect.collidepoint(mouse_x, mouse_y):
                        self.target_idx = idx

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:  # Left mouse button
                for idx, target in enumerate(targets):
                    rect = self.target_rects.get(id(target))
                    if rect and rect.collidepoint(mouse_x, mouse_y):
                        self.target_idx = idx
                        self._confirm_target()

            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.target_idx = (self.target_idx - 1) % max(1, len(targets))
                elif e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    self.target_idx = (self.target_idx + 1) % max(1, len(targets))
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if targets:
                        self._confirm_target()
                elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    # Cancel targeting mode
                    self.target_mode = False
                    self.pending_move = None
                    self.pending_user = None
            return

        # Handle move selection
        if e.type == pygame.MOUSEMOTION:
            moves = self._current_moves(self.battle_engine.battle.current_context.active_fighter)
            box_h = self.options.move_height
            box_y = self.height - box_h
            for i, move in enumerate(moves):
                x = 40 + i * 300
                y = box_y + 20
                rect = pygame.Rect(x, y, 260, 60)
                if rect.collidepoint(mouse_x, mouse_y):
                    selected_ref[0] = i

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:  # Left mouse button
            moves = self._current_moves(self.battle_engine.battle.current_context.active_fighter)
            box_h = self.options.move_height
            box_y = self.height - box_h
            for i, move in enumerate(moves):
                x = 40 + i * 300
                y = box_y + 20
                rect = pygame.Rect(x, y, 260, 60)
                if rect.collidepoint(mouse_x, mouse_y):
                    selected_ref[0] = i
                    self._start_targeting(i)

        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                selected_ref[0] = max(0, selected_ref[0] - 1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                selected_ref[0] = min(3, selected_ref[0] + 1)
            elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                selected_ref[0] = min(int(e.key - pygame.K_1), 3)
                self._start_targeting(selected_ref[0])
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._start_targeting(selected_ref[0])
            elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.exit_confirm = True

    def _get_target_rect(self, target):
        """Calculate the rectangle for a target."""
        ctx = self.battle_engine.battle.current_context
        left, right = ctx.sides[0][0], ctx.sides[1][0]
        if target == left:
            return pygame.Rect(self.width * 0.15 - 130, self.height * 0.38 - 130, 260, 260)
        elif target == right:
            return pygame.Rect(self.width * 0.85 - 130, self.height * 0.38 - 130, 260, 260)
        else:
            # Default to the center of the screen for other targets
            return pygame.Rect(self.width // 2 - 130, self.height // 2 - 130, 260, 260)

    def _draw_battle_frame(self, selected):
        ctx = self.battle_engine.battle.current_context
        self.screen.blit(self.bg, (0, 0))
        left, right = ctx.sides[0][0], ctx.sides[1][0]
        active = ctx.active_fighter
        # Determine which fighter (if any) should blink
        blink_target = None
        if self.target_mode:
            targets = self._target_list(self.pending_user or active)
            if targets:
                blink_target = targets[self.target_idx % len(targets)]
        for fv, pos in ((left, (self.width * 0.15, self.height * 0.38)), (right, (self.width * 0.85, self.height * 0.38))):
            if fv is blink_target:
                if int(pygame.time.get_ticks() / 200) % 2 == 0:
                    pass
                else:
                    self._draw_fighter(fv, pos)
            else:
                self._draw_fighter(fv, pos)
        self._draw_hp_shield(left, 60, 40); self._draw_charge(left, 60, 70)
        self._draw_hp_shield(right, self.width - 380, 40); self._draw_charge(right, self.width - 380, 70)
        self._draw_log()
        self._draw_moves(self._current_moves(active), active, selected)
        if self.exit_confirm:
            self._draw_overlay("Leave battle?  Y: yes  N: no")
        if self.battle_over:
            self._draw_overlay("Battle over! Press SPACE to return.")
        pygame.display.flip()

    # --- main loop ---
    def run(self):
        selected_move = [0]
        while True:
            dt = self.clock.tick(60) / 1000.0
            state = self.state_stack[-1]
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                if state == "title":
                    self._handle_title_event(e)
                elif state == "options":
                    self._handle_options_event(e)
                elif state == "char_select":
                    self._handle_char_select_event(e)
                elif state == "battle":
                    self._handle_battle_event(e, selected_move)
            if state == "battle":
                self._tick_anims(dt)
                self._logs(dt)
                if self.battle_engine.battle.is_battle_over:
                    self.battle_over = True
            # draw
            if state == "title":
                self._draw_title()
            elif state == "options":
                self._draw_options()
            elif state == "char_select":
                self._draw_char_select()
            elif state == "battle":
                self._draw_battle_frame(selected_move[0])

    def _set_attack(self, fv):
        v = self.views[self._fv_key(fv)]
        v["state"] = "attack"
        v["frame"] = 0
        v["timer"] = 0.0

    def _draw_overlay(self, text):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        surf = self.font.render(text, True, (240, 240, 240))
        self.screen.blit(surf, (self.width // 2 - surf.get_width() // 2, self.height // 2 - 20))

    def _tick_anims(self, dt: float):
        for v in self.views.values():
            speed = 0.25 if v["state"] == "idle" else 0.1
            v["timer"] += dt
            if v["timer"] >= speed:
                v["timer"] = 0.0
                v["frame"] = (v["frame"] + 1) % len(v[v["state"]])
                if v["state"] == "attack" and v["frame"] == 0:
                    v["state"] = "idle"

def create_engine(display_config, registry):
    return DisplayEngine(display_config, registry)
