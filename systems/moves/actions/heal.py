from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler
import math


class HealHandler(ActionHandler):
    def execute(
        self,
        engine: MoveEngine,
        action: ActionBase,
        user: FighterVolatile | None = None,
        target: FighterVolatile | None = None,
        battle_ctx: BattleContext | None = None,
        move_ctx: MoveContext | None = None,
        move: Move | None = None,
    ):
        if  user is None or target is None or battle_ctx is None or move is None:
            return False

        effective_amount = max(0, int(round(move.get_effective_amount(user, target, move_ctx))))
        gained = target.add_stat("hp", effective_amount)
        if gained <= 0:
            battle_ctx.log_stack.append(f"{user.current_fighter.name} Failed to heal")
            return False

        battle_ctx.log_stack.append(f"{target.current_fighter.name} is healed for {gained} HP")
        return True