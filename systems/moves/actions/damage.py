from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler
import math

AD_BASELINE = 1.0
AD_SCALE = 3.0
AD_SHARPNESS = 0.004
STAT_SOFT_EXPONENT = 0.9
CHARGE_INFLUENCE = 0.5

class DamageHandler(ActionHandler):
    def execute(self, engine: MoveEngine, action: ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None, battle_ctx: BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None) -> bool:
        if action is None or user is None or target is None or battle_ctx is None or move is None:
            return False
        user_stats = user.computed_stats
        target_stats = target.computed_stats

        cur_charge_user = user.current_stats.charge
        cur_charge_target = target.current_stats.charge
        max_charge_user = max(user_stats.charge, 1)

        effective_amount = move.get_effective_amount(user, target, move_ctx)

        stat_diff_raw = user_stats.attack - (target_stats.defense * (1 - action.piercing))
        soft_diff = math.copysign(abs(stat_diff_raw) ** STAT_SOFT_EXPONENT, stat_diff_raw)

        charge_delta = (cur_charge_user - cur_charge_target) / max_charge_user
        sharpness = AD_SHARPNESS * (1 + CHARGE_INFLUENCE * charge_delta)
        ad_factor = AD_BASELINE + AD_SCALE * math.tanh(sharpness * soft_diff)

        effective_damage = effective_amount * ad_factor

        if effective_damage <= 0:
            battle_ctx.log_stack.append(f"{user.current_fighter.name} Failed to deal damage")
            return False
        
        if action.is_critical:
            effective_damage *= action.crit_damage
            battle_ctx.log_stack.append("Critical Hit!")

        effective_damage = int(round(effective_damage))

        battle_ctx.log_stack.append(f"{target.current_fighter.name} takes {effective_damage} damage")
        target.take_damage(effective_damage)
        return True