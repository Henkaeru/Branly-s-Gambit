from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pydantic import BaseModel
    from .schema import Battle, BattleConfig, FighterVolatile
    from typing import Callable
    from core.registry import SystemRegistry

import inspect
import random
import warnings

# to load moves system
from .. import moves


# ------------------------------
# Battle Engine
# ------------------------------
class BattleEngine:
    """
    Responsible for:
    - Initializing a battle from a Battle schema
    - Keeping track of turn order
    - Processing player/AI events
    - Updating FighterVolatile stats
    """

    def __init__(self, config: BattleConfig, registry: SystemRegistry):
        self.config = config
        self.registry = registry

    # ------------------------------
    # Battle Lifecycle Management
    # ------------------------------

    def start(self, battle: Battle):
        """
        Initialize a battle.
        """
        self.battle = battle
        self.battle.current_context.log_stack.append("Battle started!")

    def end(self):
        """
        End the current battle.
        """
        self.battle.current_context.log_stack.append("Battle ended!")

    # ------------------------------
    # Event Queue
    # ------------------------------
    def queue_action(self, action: Callable):
        """
        Queue an action to be processed during battle processing.
        action: a callable with no arguments that performs the action
        """
        sig = inspect.signature(action)
        for param in sig.parameters.values():
            # If any parameter has no default and is not VAR_POSITIONAL or VAR_KEYWORD
            if (
                param.default is inspect.Parameter.empty
                and param.kind
                not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ):
                warnings.warn(f"Event queue contains a callable with required parameters: {action}", stacklevel=2)
                return
        self.battle.current_context.event_queue.append(action)

    def process_events(self):
        """Process all queued actions"""
        while self.battle.current_context.event_queue:
            action = self.battle.current_context.event_queue.pop(0)
            action()
            # try:
            #     action()
            # except Exception as e:
            #     warnings.warn(f"Action failed: {e}")

    # ------------------------------
    # Move Execution
    # ------------------------------
    def execute_move(self, move_id: str, user: FighterVolatile, target: FighterVolatile):
        """Execute a move from a fighter on a target"""
        move_engine = self.registry.get("moves")
        move = move_engine.set[move_id]

        # Queue the move execution
        def do_move():
            self.battle.current_context.log_stack.append(f"{user.current_fighter.name} uses {move.name} on {target.current_fighter.name}!")
            move_engine.execute(move_id, user, target, self.battle.current_context)

        self.queue_action(do_move)

    # ------------------------------
    # Battle Step
    # ------------------------------
    def step(self) -> bool:
        """
        Execute a single battle step:
        - Active fighter chooses move
        - Events are queued
        - Events are processed
        - Active fighter advances
        """
        if self.battle.is_battle_over:
            self.end()
            return False
        
        ctx = self.battle.current_context
        fighter = ctx.active_fighter

        # Skip if no moves
        if fighter.current_fighter.moves:
            # Pick random move
            move_id = random.choice(fighter.current_fighter.moves)
            # Choose opponent side randomly
            opponent_sides = [i for i in range(len(ctx.sides)) if i != ctx.active_side]
            if opponent_sides:
                target_side = random.choice(opponent_sides)
                target_fighters = ctx.sides[target_side]
                if target_fighters:
                    target = random.choice(target_fighters)
                    self.execute_move(move_id, fighter, target)

        # Process queued actions
        self.process_events()

        # Advance to next fighter in column-wise order
        self.advance_active_fighter()
        return True

    def advance_active_fighter(self):
        """
        Advance to the next active fighter in column-first order.
        """
        ctx = self.battle.current_context
        num_sides = len(self.battle.current_context.sides)
        side_idx = self.battle.current_context.active_side + 1

        # Move to next side at the same index
        while side_idx < num_sides:
            if ctx.active_fighter_index < len(ctx.sides[side_idx]):
                ctx.active_side = side_idx
                ctx.log_stack.append(f"Active fighter is now {ctx.active_fighter.current_fighter.name}")
                return
            side_idx += 1

        # No side has a fighter at this index -> increment fighter index
        ctx.active_fighter_index += 1

        # Check if the new index exists in any side
        max_index = max(len(side) for side in ctx.sides)
        if ctx.active_fighter_index >= max_index:
            # End of full turn -> increment turn and reset
            ctx.turn += 1
            ctx.active_fighter_index = 0
            ctx.active_side = 0
        else:
            # Start at first side with a fighter at the new index
            for i, side in enumerate(ctx.sides):
                if ctx.active_fighter_index < len(side):
                    ctx.active_side = i
                    ctx.log_stack.append(f"--- Turn {ctx.turn} begins ---")
                    return

def create_engine(battle_config : BaseModel, registry : SystemRegistry) -> BattleEngine:
    return BattleEngine(config=battle_config, registry=registry)