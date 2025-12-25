import json
from pathlib import Path
from .schema import Move

def load_moves(path: str) -> dict[str, Move]:
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"{path} does not exist")

    with open(path_obj, "r", encoding="utf-8") as f:
        raw_moves = json.load(f)

    moves: dict[str, Move] = {}
    for raw_move in raw_moves:
        move_id = raw_move.get("id")
        if not move_id:
            raise ValueError("Move missing required 'id' field")
        # Parse with Pydantic
        move = Move(**raw_move)
        moves[move_id] = move

    return moves