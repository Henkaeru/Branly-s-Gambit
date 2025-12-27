import random
from .action import ActionHandler


class RandomHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        weights = [c.weight() if callable(c.weight) else c.weight for c in action.choices]

        # Skip if all weights are zero
        if sum(weights) == 0: return

        choice = (random.choices(action.choices, weights=weights, k=1)[0]).action

        engine._execute_action(choice, ctx)
