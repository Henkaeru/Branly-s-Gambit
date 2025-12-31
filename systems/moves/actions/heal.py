from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler


class HealHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):

        battle_ctx.log_stack.append(f"{target.current_fighter.name} heals for {int(move_ctx.effective_amount)} HP")