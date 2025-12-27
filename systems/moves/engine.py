from .schema import Context
import random


class MoveEngine:
    def __init__(self, move_set):
        """
        move_set: MoveSet (dict-like, keyed by move.id)
        """
        self.move_set = move_set

    def execute(self, move_id: str, runtime_ctx: Context | None = None):
        """
        Execute a move by id.

        - Builds base execution context
        - Sequentially executes actions
        """
        move = self.move_set[move_id]

        if not move.enabled:
            return

        # This chance gates the entire move.
        # Action chances are independent and NOT inherited.
        if random.random() > (move.chance() if callable(move.chance) else move.chance):
            return

        # Start from default Context, then merge move overrides,
        base_ctx = Context()
        move_ctx = merge_context(base_ctx, move)
        exec_ctx = move_ctx

        if runtime_ctx is not None:
            exec_ctx = exec_ctx.model_copy(update=runtime_ctx.model_dump())

        # Execute each action in sequence
        for action in move.actions:
            self._execute_action(action, exec_ctx)

    def _execute_action(self, action, parent_ctx: Context):
        """
        Execute a single action with proper context propagation.

        - Context is merged from parent -> action
        - Action chance applies ONLY if explicitly defined
        """
        # merge context with action overrides
        ctx = merge_context(parent_ctx, action)

        # Only applies if the action explicitly defines `chance`.
        # Otherwise, action chance is implicitly 100%.
        if hasattr(action, "chance"):
            if random.random() > (action.chance() if callable(action.chance) else action.chance):
                return

        # Dispatch action execution
        self._dispatch(action, ctx)

    def _dispatch(self, action, ctx: Context):
        """
        Dispatch action execution.
        This is intentionally dumb here — real logic lives elsewhere.
        """
        # POC logging
        print(
            f"  -> action={action.id} ",
            f"target={ctx.target} ",
            f"amount={ctx.amount} ",
            f"calc={ctx.calc_target}.{ctx.calc_field} ",
            f"mult={ctx.mult} flat={ctx.flat} ",
            f"duration={ctx.duration}",
            sep="\n\t"
        )
        print(f"     full context: {ctx}")
        print(f"     action params: {action}")

def merge_context(parent: Context, obj) -> Context:
    data = parent.model_dump()
    overrides = obj.model_dump(exclude_none=True)

    for field in Context.model_fields:
        if field in overrides:
            data[field] = overrides[field]

    ctx = parent.model_copy()
    for field, value in data.items():
        setattr(ctx, field, value)
    return ctx


def create_engine(moves_config, registry):
    return MoveEngine(moves_config)
