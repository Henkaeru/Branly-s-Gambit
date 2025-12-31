from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler
import math
from ..schema import CHARGE_BONUS, STAB_BONUS

# ------------------------------
# A/D curve tuning
# ------------------------------
AD_BASELINE = 1.0
AD_SCALE = 3.0
AD_SHARPNESS = 0.004
STAT_SOFT_EXPONENT = 0.9
CHARGE_INFLUENCE = 0.5

class DamageHandler(ActionHandler):
    def execute(self, engine: MoveEngine, action: ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None, battle_ctx: BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        # Buffed maxima for attack/defense
        user_stats = user.computed_stats
        target_stats = target.computed_stats

        # Current charge values
        cur_charge_user = user.current_stats.charge
        cur_charge_target = target.current_stats.charge

        # Charge cap (buffed)
        max_charge_user = max(user_stats.charge, 1)

        # Effective amount with charge bonus (uses current charge)
        base_amount = move.get_base_amount(user, target)
        effective_amount = move.get_effective_amount(user, target)

        # Stat diff / advantage curve
        stat_diff_raw = user_stats.attack - (target_stats.defense * (1 - action.piercing))
        soft_diff = math.copysign(abs(stat_diff_raw) ** STAT_SOFT_EXPONENT, stat_diff_raw)

        # Charge delta uses current charge and max charge as denominator
        charge_delta = (cur_charge_user - cur_charge_target) / max_charge_user
        sharpness = AD_SHARPNESS * (1 + CHARGE_INFLUENCE * charge_delta)
        ad_factor = AD_BASELINE + AD_SCALE * math.tanh(sharpness * soft_diff)

        damage_float = effective_amount * ad_factor
        effective_damage = int(damage_float)

        crit_applied = False
        if action.is_critical:
            crit_applied = True
            effective_damage = int(damage_float * action.crit_damage)
            battle_ctx.log_stack.append("Critical Hit!")

        # Concise debug line
        battle_ctx.log_stack.append(
            f"[dmg] {user.current_fighter.name}→{target.current_fighter.name} "
            f"atk={user_stats.attack} def={target_stats.defense} "
            f"ch={cur_charge_user}/{max_charge_user} "
            f"base={base_amount:.1f} eff={effective_amount:.1f} "
            f"adf={ad_factor:.3f} dmg={effective_damage}"
            + (" (crit)" if crit_applied else "")
        )

        # Apply damage
        battle_ctx.log_stack.append(f"{user.current_fighter.name} deals {effective_damage} damage to {target.current_fighter.name}")
        target.take_damage(effective_damage)