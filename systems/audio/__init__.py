from core.registry import registry, SystemSpec
from .schema import AudioConfig
from .engine import create_engine as create_audio

DATA_FILE = "audio.json"

registry.add_spec(SystemSpec(
    name="audio",
    schema=AudioConfig,
    engine_factory=create_audio,
    data_file=DATA_FILE
))
