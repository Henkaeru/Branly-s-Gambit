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

        x, y = 40, 120
        for fighter in fighters:
            btn = UIButton(
                relative_rect=pygame.Rect((x, y), (180, 200)),
                text=fighter.name,
                manager=self.ui,
                object_id=f"#fighter_{fighter.id}"
            )
            btn.fighter_id = fighter.id
            self.buttons.append(btn)
            x += 200

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
        pass

    def on_exit(self):
        pass