from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pydantic import BaseModel
    from .schema import FighterSet
    from core.registry import SystemRegistry


class FighterEngine:
    def __init__(self, set: FighterSet, registry: SystemRegistry):
        self.set = set
        self.registry = registry
    
def create_engine(fighter_config : BaseModel, registry : SystemRegistry) -> FighterEngine:
    return FighterEngine(set=fighter_config, registry=registry)