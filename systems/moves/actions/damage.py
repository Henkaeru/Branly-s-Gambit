from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext
    from ..engine import MoveEngine
    
from .action import ActionHandler

class DamageHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None):
        amount = move_ctx.amount() if callable(move_ctx.amount) else move_ctx.amount
        mult = move_ctx.mult() if callable(move_ctx.mult) else move_ctx.mult
        flat = move_ctx.flat() if callable(move_ctx.flat) else move_ctx.flat
        final = amount * mult + flat

        # should use crits, and the whole ass damage calculation formula

        battle_ctx.log.append(f"{user.current_fighter.name} deals {int(final)} damage to {target.current_fighter.name}")
        target.current_stats.hp -= int(final)

