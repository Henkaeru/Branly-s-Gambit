from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler
from ...fighters.schema import Buff

class BuffHandler(ActionHandler):
    """
    Applies a flat buff (or debuff if action.reverse=True) to one or more stats.
    The magnitude is move.get_effective_amount(user, target), which already
    respects calc_target/calc_field from the effective MoveContext (percent-of-stat,
    charge, mult/flat, STAB/type, etc.).
    Buff target is always the move target (i.e., `target`).
    """
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

        buff_target = target

        # Full effective amount (percent-of-stat, charge, mult/flat, stab/type)
        amount = move.get_effective_amount(user, target)

        # Debuff support: reverse flag on the action payload
        if getattr(action, "reverse", False):
            amount = -amount

        # Normalize stats to a list
        stats: List[str] = action.stats if isinstance(action.stats, list) else [action.stats]

        # Build Buff objects with duration from move_ctx
        new_buffs = [
            Buff(stat=stat, amount=amount, duration=move_ctx.duration)
            for stat in stats
        ]

        # Append and trigger re-balance via the setter
        buff_target.current_buffs = (buff_target.current_buffs or []) + new_buffs

        # Logging
        verb = "loses" if amount < 0 else "gains"
        amt_text = f"{amount:.2f}".rstrip("0").rstrip(".")
        for stat in stats:
            battle_ctx.log_stack.append(
                f"{buff_target.current_fighter.name} {verb} {amt_text} {stat} for {move_ctx.duration} turn(s)"
            )