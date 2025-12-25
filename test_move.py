import json
from config.moves.loader import load_moves
from config.moves.schema import Action


def pretty(obj):
    """Nicely format dicts/lists as indented JSON strings."""
    return json.dumps(obj, indent=2, ensure_ascii=False)


# Load moves (already validated Move objects)
moves = load_moves("config/moves/moves.json")

print("=== RAW MOVES ===")
for move in moves.values():
    print(pretty(move.model_dump(exclude_none=True)))
    print("-" * 60)

print("\n=== VALIDATED MOVES ===")
for move in moves.values():
    print(f"✅ {move.id}: validated successfully")
    print(f"  name: {move.name}")
    print(f"  category: {move.category}")
    print(f"  target: {move.target}")
    print(f"  calc_target: {move.calc_target}")
    print(f"  actions: {len(move.actions)} action(s) loaded")

    def print_actions(actions: list[Action], indent: int = 4):
        for i, action in enumerate(actions):
            prefix = " " * indent
            print(f"{prefix}├─ action[{i}] id: {action.id}")

            params = action.params
            if params:
                print(f"{prefix}│    params:")
                for k, v in params.items():
                    print(f"{prefix}│      {k}: {v}")
            else:
                print(f"{prefix}│    params: None")

            # Recursive actions (repeat / condition)
            nested = getattr(action, "actions", None)
            if nested:
                print_actions(nested, indent + 4)

            # RandomAction choices
            choices = getattr(action, "choices", None)
            if choices:
                for j, choice in enumerate(choices):
                    print(f"{prefix}│    choice[{j}] weight: {choice.weight}")
                    print_actions([choice.action], indent + 8)

    print_actions(move.actions)
    print("└───────────────────────────────\n")




from typing import Any, Dict, List

# Example registry of action functions
ACTION_REGISTRY = {
    "attack": lambda ctx: print(f"Attack executed with amount={ctx['amount']} on {ctx['target']}"),
    "buff": lambda ctx: print(f"Buff applied to {ctx['target']} on stats {ctx.get('stat')}"),
    "status": lambda ctx: print(f"Status action: {ctx.get('status')} on {ctx['target']}"),
    "shield": lambda ctx: print(f"Shield for {ctx['target']} amount={ctx['amount']}"),
    "heal": lambda ctx: print(f"Heal {ctx['target']} by amount={ctx['amount']}"),
    "modify": lambda ctx: print(f"Modify {ctx.get('field')} to {ctx.get('value')}"),
    "condition": lambda ctx: print(f"Condition action triggered with context {ctx}"),
    "random": lambda ctx: print(f"Random action with context {ctx}"),
    "repeat": lambda ctx: print(f"Repeat action with context {ctx}"),
    "text": lambda ctx: print(f"Text action: {ctx.get('text')}")
}

def execute_move(move: Dict[str, Any], parent_context: Dict[str, Any] = None):
    """
    Recursively executes a move, merging context from outer to inner objects.
    """
    # Start with a fresh context from the move, merged with parent_context
    context = dict(parent_context or {})
    # Add all top-level fields except actions/conditions (objects)
    for k, v in move.items():
        if k != "actions":
            context[k] = v

    # Process actions (or any object list, could extend to 'conditions', etc.)
    actions: List[Dict[str, Any]] = move.get("actions", [])
    for action_obj in actions:
        # Merge action params into the context
        params = action_obj.get("params", {})
        # New context for this action (overrides parent move context)
        action_context = {**context, **params}

        # Execute the action function from registry
        action_id = action_obj["id"]
        action_fn = ACTION_REGISTRY.get(action_id)
        if action_fn:
            action_fn(action_context)
        else:
            print(f"Unknown action id: {action_id}")

        # Recursively handle nested actions inside this action (like repeat/condition)
        nested_actions = action_context.get("actions")
        if nested_actions:
            for nested in nested_actions:
                execute_move({"actions": [nested]}, parent_context=action_context)

# Example usage
move_example = {
    "id": "hp_blast",
    "amount": 0.2,
    "add": 0.05,
    "multiply": 1.5,
    "target": "opponent",
    "calc_target": "self",
    "description": "Blast equal to 20% of your HP, multiplied by 1.5, +5% of your HP",
    "actions": [
        {"id": "attack"},
        {
            "id": "status",
            "params": {
                "operation": "add",
                "status": [{"id": "burn", "params": {"amount": 0.05}}]
            }
        }
    ]
}

execute_move(moves['chaos_strike'])
