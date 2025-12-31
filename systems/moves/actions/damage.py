from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler
import math


# ------------------------------
# A/D curve tuning
# ------------------------------
AD_BASELINE = 1.0        # neutral multiplier at equal stats
AD_SCALE = 3.0           # max additional advantage from stats
AD_SHARPNESS = 0.004     # growth speed of stat advantage
STAT_SOFT_EXPONENT = 0.9 # diminishing returns on stat stacking
CHARGE_INFLUENCE = 0.5   # how much charge tilts the curve

class DamageHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        effective_amount = move.get_effective_amount(user, target)
        stat_diff = user.current_fighter.stats.attack - (target.current_fighter.stats.defense * (1 - action.piercing))
        stat_diff = math.copysign(abs(stat_diff) ** STAT_SOFT_EXPONENT, stat_diff)
        charge_delta = (user.current_stats.charge - target.current_stats.charge) / user.base_fighter.stats.charge
        sharpness = AD_SHARPNESS * (1 + CHARGE_INFLUENCE * charge_delta)
        ad_factor = AD_BASELINE + AD_SCALE * math.tanh(sharpness * stat_diff)

        effective_damage = int(effective_amount * ad_factor)
        if action.is_critical:
            effective_damage = int(effective_damage * action.crit_damage)
            battle_ctx.log_stack.append(f"Critical Hit!")

        battle_ctx.log_stack.append(f"{user.current_fighter.name} deals {effective_damage} damage to {target.current_fighter.name}")
        target.take_damage(effective_damage)