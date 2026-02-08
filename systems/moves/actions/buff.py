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
        if action is None or user is None or target is None or battle_ctx is None or move_ctx is None or move is None:
            return False  # Cannot execute without action/user/target/battle_ctx/move_ctx/move

        buff_target = target

        # Full effective amount (percent-of-stat, charge, mult/flat, stab/type)
        amount = int(round(move.get_effective_amount(user, target, move_ctx)))

        if amount <= 0:
            battle_ctx.log_stack.append(f"{user.current_fighter.name} Failed to {"debuff" if action.reverse else "buff"}")
            return False

        # Debuff support: reverse flag on the action payload
        if action.reverse:
            amount = -amount

        # Normalize stats to a list
        stats: List[str] = action.stats if isinstance(action.stats, list) else [action.stats]

        # Duration semantics: duration 1 should expire at end of the *next* turn.
        raw_duration = move_ctx.duration
        adj_duration = raw_duration if raw_duration <= 0 else raw_duration + 1

        # Build Buff objects with duration from move_ctx
        new_buffs = [
            Buff(stat=stat, amount=amount, duration=adj_duration)
            for stat in stats
        ]

        # Append and trigger re-balance via the setter
        buff_target.current_buffs = (buff_target.current_buffs or []) + new_buffs

        # Logging
        verb = "loses" if amount < 0 else "gains"
        for stat in stats:
            battle_ctx.log_stack.append(
                f"{buff_target.current_fighter.name} {verb} {amount} {stat} for {raw_duration} turn(s)"
            )
        return True