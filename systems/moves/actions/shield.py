from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext
    from ..engine import MoveEngine
    
from .action import ActionHandler


class ShieldHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None):
        amount = move_ctx.amount() if callable(move_ctx.amount) else move_ctx.amount
        mult = move_ctx.mult() if callable(move_ctx.mult) else move_ctx.mult
        flat = move_ctx.flat() if callable(move_ctx.flat) else move_ctx.flat
        final = amount * mult + flat

        # should add to doc that max shield is 999
        # should ensure max shield is 999

        battle_ctx.log.append(f"{target.current_fighter.name} gains a shield of {int(final)} HP")