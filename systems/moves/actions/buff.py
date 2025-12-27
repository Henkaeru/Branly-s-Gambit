from .action import ActionHandler


class BuffHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        amount = ctx.amount() if callable(ctx.amount) else ctx.amount
        target = ctx.target() if callable(ctx.target) else ctx.target
        stat = action.stat() if callable(action.stat) else action.stat

        # amount of buff is supposed to be able to be negative (debuff) but amount is always positive
        # should check calc_target and calc_field
        # max 4 stack for buffs + debuffs on an entity

        print(f"Applying buff: {stat} +{amount} to {target}")