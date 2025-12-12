import json
from pathlib import Path
from typing import Union
from dataclasses import asdict, is_dataclass

from .schema import DummyConfig, DummyGroup, DummySubItem


def _dict_to_dummyconfig(data: dict) -> DummyConfig:
    """Recursively instantiate dataclasses from dict."""
    groups = {}
    for key, group_data in data.get("groups", {}).items():
        items = [DummySubItem(**item) for item in group_data.get("items", [])]
        groups[key] = DummyGroup(
            name=group_data["name"],
            description=group_data.get("description"),
            items=items,
            priority=group_data.get("priority", 0),
        )
    return DummyConfig(
        version=data["version"],
        enabled=data.get("enabled", True),
        global_metadata=data.get("global_metadata", {}),
        groups=groups,
    )


def load_dummy_config(path: Union[str, Path] = None) -> DummyConfig:
    """Load and parse the dummy config JSON file."""
    path = Path(path or Path(__file__).parent / "example.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _dict_to_dummyconfig(data)


def save_dummy_config(config: DummyConfig, path: Union[str, Path]):
    """Serialize and save DummyConfig back to JSON."""
    def dataclass_to_dict(obj):
        if is_dataclass(obj):
            return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [dataclass_to_dict(v) for v in obj]
        elif isinstance(obj, dict):
            return {k: dataclass_to_dict(v) for k, v in obj.items()}
        else:
            return obj

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataclass_to_dict(config), f, indent=2)
