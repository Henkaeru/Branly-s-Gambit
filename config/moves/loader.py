import json
from pathlib import Path
from .schema import MoveModel, ActionModel, StatusModel, ConditionModel
from .default import DEFAULTS
from typing import Dict, Any

def load_moves(path: str) -> Dict[str, Dict[str, Any]]:
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"{path} does not exist")

    with open(path_obj, "r", encoding="utf-8") as f:
        raw_moves = json.load(f)

    merged_moves: Dict[str, Dict[str, Any]] = {}
    for raw_move in raw_moves:
        # Merge defaults first
        move_ctx = {**DEFAULTS, **raw_move}
        move_id = move_ctx.get("id")
        if not move_id:
            raise ValueError("Move missing required 'id' field")
        merged_moves[move_id] = move_ctx

    return merged_moves
