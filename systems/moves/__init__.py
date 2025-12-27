from core.registry import registry, SystemSpec
from .schema import MoveSet
from .engine import create_engine as create_moves

DATA_FILE = "moves.json"

registry.add_spec(SystemSpec(
    name="moves",
    schema=MoveSet,
    engine_factory=create_moves,
    data_file=DATA_FILE
))