from .action import ActionHandler


class StatusHandler(ActionHandler):
    def execute(self, action, ctx, engine):
        amount = ctx.amount() if callable(ctx.amount) else ctx.amount
        mult = ctx.mult() if callable(ctx.mult) else ctx.mult
        flat = ctx.flat() if callable(ctx.flat) else ctx.flat
        target = ctx.target() if callable(ctx.target) else ctx.target

        operation = action.operation() if callable(action.operation) else action.operation
        status = [s.id() if callable(s.id) else s.id for s in action.status]


        final = amount * mult + flat

        # should ensure we respect the doc status application rules
        # don't care about amount when removing

        print(f"{'Applying' if operation == 'add' else 'Removing'} status '{status}' {'to' if operation == 'add' else 'from'} {target} {f'for {final} turns!' if operation == 'add' else '!'}")