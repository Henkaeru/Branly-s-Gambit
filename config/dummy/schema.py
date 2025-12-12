from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DummySubItem:
    """Represents a child entry inside a dummy configuration group."""
    id: str
    value: str
    tags: List[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class DummyGroup:
    """A collection of sub-items, with optional metadata."""
    name: str
    description: Optional[str] = None
    items: List[DummySubItem] = field(default_factory=list)
    priority: int = 0


@dataclass
class DummyConfig:
    """Top-level dummy configuration container."""
    version: str
    enabled: bool = True
    global_metadata: Dict[str, str] = field(default_factory=dict)
    groups: Dict[str, DummyGroup] = field(default_factory=dict)

    def get_group(self, name: str) -> Optional[DummyGroup]:
        return self.groups.get(name)

    def all_items(self) -> List[DummySubItem]:
        """Flatten and return all items across all groups."""
        return [item for group in self.groups.values() for item in group.items]
