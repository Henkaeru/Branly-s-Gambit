from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler


class BuffHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        # amount of buff is supposed to be able to be negative (debuff) but amount is always positive
        # should check calc_target and calc_field
        # max 4 stack for buffs + debuffs on an entity
        # buffs last for duration turns
        for stat in action.stats:
            calc_target = move_ctx.get_calc_target(user, target)
            battle_ctx.log_stack.append(f"{target.current_fighter.name} gains +{f'{move_ctx.get_base_amount()}{f'% of{f' {move_ctx.calc_target}' if move_ctx.calc_target == 'opponent' else ''} {calc_target.current_fighter.name}\'s {move_ctx.calc_field}' if move_ctx.is_percentage else ''}'} as {stat}{f' for {move_ctx.duration} turns' if not move_ctx.is_infinite_duration else ''} !")