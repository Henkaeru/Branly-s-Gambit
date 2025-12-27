import random
from pydantic import BaseModel
from core.registry import SystemRegistry
from .schema import Fighter, FighterSet


class FighterEngine:
    def __init__(self, fighter_set: FighterSet):
        self.fighter_set = fighter_set

    def take_damage(self, fighter_id: str, amount: int):
        fighter = self.fighter_set[fighter_id]
        fighter.stats.hp = max(0, fighter.stats.hp - amount)

    def heal(self, fighter_id: str, amount: int):
        fighter = self.fighter_set[fighter_id]
        fighter.stats.hp += amount

    def random_target(self) -> Fighter:
        return random.choice(self.fighter_set.fighters)
    
def create_engine(fighter_config : BaseModel, registry : SystemRegistry) -> FighterEngine:
    return FighterEngine(fighter_set=fighter_config)