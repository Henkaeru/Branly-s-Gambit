from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext
    from ..engine import MoveEngine
    
from .action import ActionHandler


class BuffHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None):
        amount = move_ctx.amount() if callable(move_ctx.amount) else move_ctx.amount
        stat = action.stat() if callable(action.stat) else action.stat

        # amount of buff is supposed to be able to be negative (debuff) but amount is always positive
        # should check calc_target and calc_field
        # max 4 stack for buffs + debuffs on an entity
        # buffs last for duration turns

        battle_ctx.log.append(f"{target.current_fighter.name} gains +{amount if isinstance(amount, int) else f'{amount*100:.1f}%'} {stat} buff")