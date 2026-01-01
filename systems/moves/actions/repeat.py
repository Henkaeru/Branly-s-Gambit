from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler


class RepeatHandler(ActionHandler):
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
        if action is None:
            return False

        any_success = False
        for _ in range(int(round(action.count))):
            for sub_action in action.actions:
                res = engine._execute_action(sub_action, user, target, battle_ctx, move_ctx, move)
                any_success = any_success or bool(res)

        return any_success