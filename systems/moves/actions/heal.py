from .action import ActionHandler


class HealHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        amount = ctx.amount() if callable(ctx.amount) else ctx.amount
        mult = ctx.mult() if callable(ctx.mult) else ctx.mult
        flat = ctx.flat() if callable(ctx.flat) else ctx.flat
        target = ctx.target() if callable(ctx.target) else ctx.target

        final = amount * mult + flat

        print(f"Healing {target} for {final} HP!")