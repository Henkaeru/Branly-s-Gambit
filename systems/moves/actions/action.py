from abc import ABC, abstractmethod
from ..schema import Context

class ActionHandler(ABC):
    @abstractmethod
    def execute(self, action, ctx: Context, engine):
        ...
