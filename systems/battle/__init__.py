from core.registry import registry, SystemSpec
from .schema import BattleConfig
from .engine import create_engine as create_battle

DATA_FILE = "battle.json"

registry.add_spec(SystemSpec(
    name="battle",
    schema=BattleConfig,
    engine_factory=create_battle,
    data_file=DATA_FILE
))