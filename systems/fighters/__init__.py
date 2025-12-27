from core.registry import registry, SystemSpec
from .schema import FighterSet
from .engine import create_engine as create_fighters

DATA_FILE = "fighters.json"

registry.add_spec(SystemSpec(
    name="fighters",
    schema=FighterSet,
    engine_factory=create_fighters,
    data_file=DATA_FILE
))