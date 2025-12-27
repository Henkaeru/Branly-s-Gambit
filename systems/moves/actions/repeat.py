from .action import ActionHandler


class RepeatHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        count = action.count() if callable(action.count) else action.count

        for _ in range(int(count)):
            for sub_action in action.actions:
                engine._execute_action(sub_action, ctx)