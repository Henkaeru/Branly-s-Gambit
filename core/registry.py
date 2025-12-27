from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Type
from pydantic import BaseModel


@dataclass
class SystemSpec:
    name: str
    schema: Type[BaseModel]
    engine_factory: Callable[[Any, "SystemRegistry"], Any]
    data_file: str

class SystemRegistry:
    def __init__(self, data_root: Path):
        self._systems: dict[str, Any] = {}
        self._specs: dict[str, SystemSpec] = {}
        self._data_root = data_root

    def add_spec(self, spec: SystemSpec):
        if spec.name in self._specs:
            raise ValueError(f"System '{spec.name}' already registered")
        self._specs[spec.name] = spec

    def _load_config(self, spec: SystemSpec):
        path = self._data_root / spec.data_file
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open() as f:
            raw = json.load(f)

        return spec.schema.model_validate(raw)
    
    def build(self, name: str):
        if name in self._systems:
            return self._systems[name]

        if name not in self._specs:
            raise ValueError(f"System '{name}' not registered")

        spec = self._specs[name]
        config = self._load_config(spec)
        engine = spec.engine_factory(config, self)
        self._systems[name] = engine
        return engine
    
    def build_all(self):
        for name in self._specs:
            self.build(name)

    def get(self, name: str) -> Any:
        if not name in self._systems:
            self.build(name)
        
        return self._systems[name]

# -------------------
# singleton instance
DATA_ROOT = Path(__file__).parent.parent / "data"
registry = SystemRegistry(DATA_ROOT)