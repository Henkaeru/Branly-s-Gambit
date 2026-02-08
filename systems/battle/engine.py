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
from enum import Enum

# to load moves system
from .. import moves


# ------------------------------
# Battle Mode Enum
# ------------------------------
class BattleMode(Enum):
    AUTO = "auto"
    LOCAL_1V1 = "local_1v1"


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
        self.battle_mode = BattleMode.AUTO  # Default mode

    # ------------------------------
    # Battle Mode Management
    # ------------------------------
    def set_battle_mode(self, mode: BattleMode):
        """Switch between battle modes"""
        self.battle_mode = mode
        self.battle.current_context.log_stack.append(f"Battle mode set to: {mode.value}")

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

    def get_available_moves(self, fighter: FighterVolatile) -> list[tuple[int, str, str]]:
        """Get list of available moves for a fighter with their indices and names"""
        if not fighter.current_fighter.moves:
            return []
        
        move_engine = self.registry.get("moves")
        moves_info = []
        for idx, move_id in enumerate(fighter.current_fighter.moves, 1):
            move = move_engine.set.get(move_id)
            move_name = move.name if move else move_id
            moves_info.append((idx, move_id, move_name))
        return moves_info

    def manual_move_selection(self, fighter: FighterVolatile) -> tuple[str, FighterVolatile] | None:
        """
        Handle manual move selection for local 1v1 mode.
        Returns (move_id, target) or None if selection failed.
        """
        ctx = self.battle.current_context
        moves_info = self.get_available_moves(fighter)
        
        if not moves_info:
            self.battle.current_context.log_stack.append(f"{fighter.current_fighter.name} has no moves!")
            return None

        # Display available moves
        print(f"\n{fighter.current_fighter.name}'s turn:")
        for idx, move_id, move_name in moves_info:
            print(f"  {idx}. {move_name}")

        # Get move selection
        try:
            choice = int(input(f"Select move (1-{len(moves_info)}): "))
            if 1 <= choice <= len(moves_info):
                selected_move_id = moves_info[choice - 1][1]
            else:
                print("Invalid choice! Using first move.")
                selected_move_id = moves_info[0][1]
        except (ValueError, EOFError):
            print("Invalid input! Using first move.")
            selected_move_id = moves_info[0][1]

        # Get random opponent
        opponent_sides = [i for i in range(len(ctx.sides)) if i != ctx.active_side]
        if opponent_sides:
            target_side = random.choice(opponent_sides)
            target_fighters = ctx.sides[target_side]
            if target_fighters:
                target = random.choice(target_fighters)
                return (selected_move_id, target)
        
        return None

    def _pick_default_target(self, user: FighterVolatile) -> FighterVolatile | None:
        ctx = self.battle.current_context
        opponent_sides = [i for i in range(len(ctx.sides)) if i != ctx.active_side]
        for side_idx in opponent_sides:
            for fv in ctx.sides[side_idx]:
                if fv.alive:
                    return fv
        return None

    # ------------------------------
    # Battle Step
    # ------------------------------
    def step(self, selected_action: tuple[str, FighterVolatile] | None = None) -> bool:
        """
        Execute a single battle step.
        selected_action: optional (move_id, target) chosen externally (e.g., UI)
        """
        if self.battle.is_battle_over:
            self.end()  # End the battle if it's over
            return False
        
        ctx = self.battle.current_context
        fighter = ctx.active_fighter

        # Externally provided move/target (preferred when present)
        if selected_action:
            move_id, target = selected_action
            target = target or self._pick_default_target(fighter)
            if target:
                self.execute_move(move_id, fighter, target)

        # Legacy/manual selection
        elif self.battle_mode == BattleMode.LOCAL_1V1:
            result = self.manual_move_selection(fighter)
            if result:
                move_id, target = result
                self.execute_move(move_id, fighter, target)

        else:
            # Auto mode: AI selects randomly
            if fighter.current_fighter.moves:
                move_id = random.choice(fighter.current_fighter.moves)
                target = self._pick_default_target(fighter)
                if target:
                    self.execute_move(move_id, fighter, target)

        self.process_events()
        self.advance_active_fighter()
        return True

    def _tick_all_buffs(self):
        """Tick buffs for every fighter in the current battle context."""
        for side in self.battle.current_context.sides:
            for fv in side:
                fv.tick_buffs(self.battle.current_context.log_stack)

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
            self._tick_all_buffs()
        else:
            # Start at first side with a fighter at the new index
            for i, side in enumerate(ctx.sides):
                if ctx.active_fighter_index < len(side):
                    ctx.active_side = i
                    ctx.log_stack.append(f"--- Turn {ctx.turn} begins ---")
                    return

def create_engine(battle_config : BaseModel, registry : SystemRegistry) -> BattleEngine:
    return BattleEngine(config=battle_config, registry=registry)