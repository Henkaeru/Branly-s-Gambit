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
        
        self.fighter_name_labels = {}
        self.selected_move_idx = 0
        self.battle_over = False

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
        self.move_buttons.clear()

        ctx = self.battle_engine.battle.current_context
        user = ctx.active_fighter
        moves = self.controller.current_moves(user)

        for i, move in enumerate(moves):
            btn = UIButton(
                relative_rect=pygame.Rect(20 + i * 300, 20, 260, 60),
                text=f"{move.name} ({move.charge_usage})",
                manager=self.ui,
                container=self.action_bar
            )
            btn.move_idx = i
            self.move_buttons.append(btn)
            self.ui_elements.append(btn)

    def _build_log_box(self):
        w, h = self.engine.window_size

        self.log_box = UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, h - 300, w - 20, 160),
            manager=self.ui
        )
        self.ui_elements.append(self.log_box)

    def update(self, dt):
        self.renderer.update(dt)
        
        self.controller.update_logs(dt)
        logs = self.controller.visible_logs()
        self.log_box.set_text("<br>".join(logs))

        if self.battle_engine.battle.is_battle_over:
            self.battle_over = True

    def process_event(self, event):
        if self.battle_over:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                from .title import TitleScreen
                self.engine.set_screen(TitleScreen)
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

    def draw(self, surface):
        self.renderer.draw(surface, self.controller)

    def _build_buffs_and_statuses_ui(self, fv, center_x, y):
        # Clear old icons for this fighter
        icons = getattr(self, "_status_icons", {})
        for el in icons.get(id(fv), []):
            el.kill()

        icons[id(fv)] = []
        self._status_icons = icons

        effects = fv.current_buffs + fv.current_status
        if not effects:
            return

        icon_size = 32
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

            rect = pygame.Rect(
                start_x + i * (icon_size + padding),
                y,
                icon_size,
                icon_size
            )

            img = UIImage(
                relative_rect=rect,
                image_surface=surface,
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

            img.set_tooltip(tooltip)

            icons[id(fv)].append(img)
            self.ui_elements.append(img)

    
    def _update_fighter_name_ui(self, fv, center_x, top_y):
        label = self.fighter_name_labels.get(id(fv))

        battle = self.battle_engine.battle
        is_active = fv is battle.current_context.active_fighter

        rect = pygame.Rect(center_x - 120, top_y, 240, 30)

        if label is None:
            label = UILabel(
                relative_rect=rect,
                text=fv.current_fighter.name,
                manager=self.ui
            )
            self.fighter_name_labels[id(fv)] = label
            self.ui_elements.append(label)
        else:
            label.set_relative_position(rect.topleft)

        # color via theme or fallback
        label.set_text(fv.current_fighter.name)
        label.text_colour = (
            self.theme.colour("label_active")
            if is_active
            else self.theme.colour("label_normal")
        )
        label.rebuild()

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
        self.bg = self.engine._load_image(
            battle.background_sprite,
            size=self.engine.window_size
        )

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

        self._draw_fighter(left, (self.engine.window_size[0] * 0.15, self.engine.window_size[1] * 0.38))
        self._draw_fighter(right, (self.engine.window_size[0] * 0.85, self.engine.window_size[1] * 0.38))

        self._draw_hp(left, 60, 40)
        self._draw_shield(left, 60, 40)
        self._draw_charge(left, 60, 70)

        right_x = self.engine.window_size[0] - 380
        self._draw_hp(right, right_x, 40)
        self._draw_shield(right, right_x, 40)
        self._draw_charge(right, right_x, 70)

        if controller.target_mode:
            self._draw_target_highlight(controller)
    
    def build_view(self, fv, flip=False):
        base = self.engine._load_image(
            fv.current_fighter.fighter_sprite,
            size=(260, 260),
            flip=flip
        )

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
        view = self.views[id(fv)]

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

        base_radius = 46
        radius = base_radius + pulse * 6

        width = int(radius * 2.2)
        height = int(radius * 0.55)
        alpha = int(110 + pulse * 70)

        ring = pygame.Surface((width, height), pygame.SRCALPHA)
        ring_color = self.engine.theme.colour("target_ring")

        if len(ring_color) == 4:
            r, g, b, _ = ring_color
        else:
            r, g, b = ring_color

        pygame.draw.ellipse(
            ring,
            (r, g, b, alpha),
            ring.get_rect(),
            width=3
        )

        target = controller.current_target()
        if not target:
            return

        anchor = self.fighter_anchors.get(id(target))
        if not anchor:
            return

        rect = ring.get_rect(center=anchor)
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
        new_logs = ctx.get_next_logs()
        if new_logs:
            self.pending_logs.extend(new_logs)

        self.log_timer -= dt
        if self.log_timer <= 0 and self.pending_logs:
            self.log_lines.append(self.pending_logs.pop(0))
            self.log_timer = self.log_interval

    def visible_logs(self):
        return self.log_lines[-6:]