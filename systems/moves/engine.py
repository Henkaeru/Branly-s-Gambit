from __future__ import annotations
from typing import TYPE_CHECKING
import warnings
if TYPE_CHECKING:
    from pydantic import BaseModel
    from .schema import ActionBase, MoveSet
    from ..battle.schema import BattleContext, FighterVolatile
    from .actions.action import ActionHandler
    from core.registry import SystemRegistry

from .schema import Move, MoveContext
from .handlers import ACTION_HANDLERS
import random


class MoveEngine:
    def __init__(self, set : MoveSet, registry: SystemRegistry, action_handlers: ActionHandler| None = None):
        """
        set: MoveSet (dict-like, keyed by move.id)
        """
        self.set = set
        self.registry = registry
        self.action_handlers = action_handlers or {}

    def execute(self, move_id: str, user: FighterVolatile | None = None, target: FighterVolatile | None = None, battle_ctx: BattleContext | None = None, runtime_ctx: MoveContext | None = None):
        """
        Execute a move by id.

        - battle_ctx: full battle context, for battle-aware logic
        - runtime_ctx: MoveContext overrides (per move execution)
        """
        move = self.set[move_id]
        if user and move.charge_usage > user.current_stats.charge:
            battle_ctx.log_stack.append(f"{user.current_fighter.name} does not have enough charge to use {move.name}. Required: {move.charge_usage}, Available: {user.current_stats.charge}")
            return

        # This chance gates the entire move.
        # Action chances are independent and NOT inherited.
        if random.random() > move.chance:
            return

        # Start from default Context, then merge move overrides,
        base_ctx = MoveContext()
        move_ctx = merge_context(base_ctx, move)
        exec_ctx = move_ctx

        if runtime_ctx is not None:
            exec_ctx = exec_ctx.model_copy(update=runtime_ctx.model_dump())

        # Execute each action in sequence
        for action in move.actions:
            self._execute_action(action, user, target, battle_ctx, exec_ctx, move)

    def _execute_action(self, action: ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx: BattleContext | None = None, parent_ctx: MoveContext | None = None, move: Move | None = None):
        """
        Execute a single action with proper context propagation.
        """
        if not action:
            raise RuntimeError("Cannot execute empty action")
        # merge context with action overrides
        ctx = merge_context(parent_ctx, action)

        # Only applies if the action explicitly defines `chance`.
        # Otherwise, action chance is implicitly 100%.
        if hasattr(action, "chance"):
            if random.random() > (action.chance() if callable(action.chance) else action.chance):
                return

        # Dispatch action execution
        self._dispatch(action, user, target, battle_ctx, ctx, move)

    def _dispatch(self, action: ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx: BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        """
        Dispatch action execution.
        This is intentionally dumb here — real logic lives elsewhere.
        """
        handler = self.action_handlers.get(action.id)
        if not handler:
            raise RuntimeError(f"No handler registered for action '{action.id}'")

        handler.execute(self, action, user, target, battle_ctx, move_ctx, move)

def merge_context(parent: MoveContext, obj) -> MoveContext:
    base = parent.model_dump()
    overrides = obj.model_dump(exclude_none=True)

    for field in MoveContext.model_fields:
        if field in overrides:
            base[field] = overrides[field]

    return MoveContext.model_validate(base)

def create_engine(moves_config : BaseModel, registry : SystemRegistry) -> MoveEngine:
    return MoveEngine(set=moves_config, registry=registry, action_handlers=ACTION_HANDLERS)
