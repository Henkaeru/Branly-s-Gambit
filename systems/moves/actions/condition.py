from .action import ActionHandler


class ConditionHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        for condition in action.conditions:
            condition_id = condition.id() if callable(condition.id) else condition.id
            condition_value = condition.value() if callable(condition.value) else condition.value
            print(f"Evaluating condition '{condition_id}' with value '{condition_value}'")
            # if not check_condition(condition.id, condition.value if callable(condition.value) else condition.value, ctx): return

            # Evaluate all conditions with AND logic
            # If any condition is False, the overall result is False
            # Evaluation are based on condition, values pairs

        for sub_action in action.actions:
            engine._execute_action(sub_action, ctx)