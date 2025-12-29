from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext
    from ..engine import MoveEngine
    
from .action import ActionHandler


class StatusHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None):
        amount = move_ctx.amount() if callable(move_ctx.amount) else move_ctx.amount
        mult = move_ctx.mult() if callable(move_ctx.mult) else move_ctx.mult
        flat = move_ctx.flat() if callable(move_ctx.flat) else move_ctx.flat
        operation = action.operation() if callable(action.operation) else action.operation
        status = [s.id() if callable(s.id) else s.id for s in action.status]


        final = amount * mult + flat

        # should ensure we respect the doc status application rules
        # don't care about amount when removing

        battle_ctx.log.append(f"{'Applying' if operation == 'add' else 'Removing'} status '{status}' {'to' if operation == 'add' else 'from'} {target.current_fighter.name} {f'for {final} turns!' if operation == 'add' else '!'}")