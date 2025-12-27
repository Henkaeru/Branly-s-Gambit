from .action import ActionHandler


class ModifyHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        field = action.field() if callable(action.field) else action.field
        value = action.value() if callable(action.value) else action.value

        # Complicated asf logic for modifying a field on a target
        # So not gonna implement it fully for now

        print(f"Modifying  {field} to {value}")