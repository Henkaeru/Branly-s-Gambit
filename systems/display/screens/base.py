from abc import ABC, abstractmethod

class Screen(ABC):
    def __init__(self, engine):
        self.engine = engine
        self.ui = engine.ui
        self.theme = engine.theme

    @abstractmethod
    def on_enter(self): ...
    @abstractmethod
    def on_exit(self): ...
    @abstractmethod
    def process_event(self, event): ...
    @abstractmethod
    def update(self, dt): ...
    @abstractmethod
    def draw(self, surface): ...
