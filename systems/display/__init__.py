from core.registry import registry, SystemSpec
from .schema import DisplayConfig
from .engine import create_engine as create_display

DATA_FILE = "display.json"

registry.add_spec(SystemSpec(
    name="display",
    schema=DisplayConfig,
    engine_factory=create_display,
    data_file=DATA_FILE
))
