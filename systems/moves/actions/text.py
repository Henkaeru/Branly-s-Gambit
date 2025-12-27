from .action import ActionHandler


class TextHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        text = action.text() if callable(action.text) else action.text
        style = action.style() if callable(action.style) else action.style

        print(f"writing {text} with style: {style}")