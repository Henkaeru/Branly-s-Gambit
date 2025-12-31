from __future__ import annotations
from pydantic import Field, model_validator
from typing import Callable, Optional
from core.dsl.random_dsl import RINT, RNUM, RSTR, RVAL, check
import copy
import inspect
import warnings

from core.dsl.resolvable import ResolvableModel
from ..fighters.schema import Buff, Fighter, FighterStats, Status
from core.registry import registry

TYPE = ("dev", "opti", "syst", "data", "proj", "team", "none")
MAX_BUFFS = 4
MAX_SIDE = 2
MAX_TURN = 30

# to load fighters system
import systems.fighters

# ------------------------------
# Fighter Volatile
# ------------------------------
class FighterVolatile(ResolvableModel):
    base_id: str

    current_fighter: Optional[Fighter] = None # mutable, per-battle fighter
    current_buffs: list[Buff] = None  # mutable, per-battle buffs
    current_status: list[Status] = None # mutable, per-battle status effects

    # Private backing fields for properties
    _current_buffs: list[Buff] = None  # mutable, per-battle buffs
    _current_status: list[Status] = None # mutable, per-battle status effects

    def model_post_init(self, __context=None):
        base = self.base_fighter
        if base is None:
            raise ValueError(f"FighterVolatile references unknown fighter id: {self.base_id}")

        # --- Merge current_fighter with base ---
        if self.current_fighter is None:
            self.current_fighter = copy.deepcopy(base)
            self.current_fighter.stats = copy.deepcopy(base.starting_stats)
        else:
            # merge: keep overrides, fill missing with base
            base_data = base.model_dump()
            override_data = self.current_fighter.model_dump()
            merged_data = {**base_data, **override_data}

            # merge stats separately: starting_stats + override
            merged_stats = copy.deepcopy(base.starting_stats)
            if override_data.get("stats"):
                for k, v in override_data["stats"].model_dump().items():
                    merged_stats.__setattr__(k, v)
            merged_data["stats"] = merged_stats

            self.current_fighter = Fighter(**merged_data)

        # --- Merge buffs/status ---
        base_buffs = copy.deepcopy(base.starting_buffs)
        base_status = copy.deepcopy(base.starting_status)

        self._current_buffs = (self._current_buffs or []) + base_buffs
        self._current_status = (self._current_status or []) + base_status
            
    @property
    def base_fighter(self) -> Optional[Fighter]:
        return registry.get("fighters").set.get(self.base_id, None)
    @property
    def current_stats(self) -> FighterStats:
        return self.current_fighter.stats
    @current_stats.setter
    def current_stats(self, new_stats: FighterStats):
        for k, v in new_stats.model_dump().items():
            setattr(self.current_fighter.stats, k, v)
        FighterStats.model_validate(self.current_fighter.stats)
    @property
    def computed_stats(self) -> FighterStats:
        """
        Compute all stats with buffs applied proportionally.
        """
        stats = copy.deepcopy(self.current_stats)

        for buff in self._current_buffs or []:
            if buff.stat not in stats.model_fields:
                continue

            base_value = getattr(self.current_stats, buff.stat)
            buffed_value = base_value + buff.amount  # all buffs are flat amounts

            # Maintain ratio: new / old
            setattr(stats, buff.stat, buffed_value)

        FighterStats.model_validate(stats)
        return stats
    @property
    def current_buffs(self) -> list[Buff]:
        return self._current_buffs
    @current_buffs.setter
    def current_buffs(self, value: list[Buff]):
        for i, buff in enumerate(value):
            if i < len(self.current_buffs):
                self.current_buffs[i] = buff
            else:
                self.current_buffs.append(buff)
        if len(self.current_buffs) > MAX_BUFFS:
            self.current_buffs = self.current_buffs[:MAX_BUFFS]
    @property
    def current_status(self) -> list[Status]:
        return self._current_status
    @current_status.setter
    def current_status(self, value: list[Status]):
        for i, status in enumerate(value):
            if i < len(self.current_status):
                self.current_status[i] = status
            else:
                self.current_status.append(status)
    @property
    def current_moves(self) -> list[str]:
        return self.current_fighter.moves
    @current_moves.setter
    def current_moves(self, new_moves: list[str]):
        for i, move in enumerate(new_moves):
            if i < len(self.current_fighter.moves):
                self.current_fighter.moves[i] = move
            else:
                self.current_fighter.moves.append(move)
        Fighter.model_validate(self.current_fighter)
    @property
    def alive(self) -> bool:
        return self.computed_stats.hp > 0
    @property
    def has_shield(self) -> bool:
        return self.computed_stats.shield > 0

    def _apply_stat_delta(self, stat: str, delta: int):
        """
        Apply delta to a stat as if modifying computed_stats,
        but actually update current_stats proportionally.
        """
        current_value = getattr(self.current_stats, stat)
        computed_value = getattr(self.computed_stats, stat)

        if computed_value == 0:
            # Avoid division by zero
            setattr(self.current_stats, stat, max(0, current_value + delta))
            return

        # Determine the ratio in current_stats relative to computed_stats
        ratio = current_value / computed_value
        # Apply delta to computed_value, then scale back to current_stats
        new_computed = computed_value + delta
        new_current = int(new_computed * ratio)
        # Clamp to 0..new_computed
        new_current = max(0, min(new_current, new_computed))
        setattr(self.current_stats, stat, new_current)


    def take_damage(self, amount: int):
        if self.has_shield:
            shield_before = self.current_stats.shield
            if amount >= shield_before:
                amount -= shield_before
                self.current_stats.shield = 0
            else:
                self.current_stats.shield -= amount
                amount = 0
        self.current_stats.hp -= amount
        if self.current_stats.hp < 0:
            self.current_stats.hp = 0
    
    @model_validator(mode="before")
    @classmethod
    def validate_id_or_abort(cls, data):
        base_id = data.get("base_id", "")
        fighter_set = registry.get("fighters").set
        if base_id not in fighter_set:
            warnings.warn(f"Fighter id '{base_id}' not found.", stacklevel=2)
            return None
        return data
    
    @model_validator(mode="after")
    def check_volatile(self):
        if not self.base_fighter:
            raise ValueError(f"FighterVolatile references unknown fighter id: {self.base_id}")
        if len(self._current_buffs) > MAX_BUFFS:
            warnings.warn(f"FighterVolatile '{self.base_id}' has more than {MAX_BUFFS} buffs.", stacklevel=2)
            self._current_buffs = self._current_buffs[:MAX_BUFFS]
        return self

# ------------------------------
# Battle Context
# ------------------------------
class BattleContext(ResolvableModel):
    turn: RINT = 0
    active_side: RINT = "l[0, 1]"  # "left" or "right"
    active_fighter_index: RINT = 0

    sides: list[list[FighterVolatile]] = Field(default_factory=dict) # "left" and "right" sides

    event_queue: list[Callable] = Field(default_factory=list)  # queued actions to process
    log_stack: list[str] = Field(default_factory=list)  # current log stack
    log_history: list[str] = Field(default_factory=list)  # full log history

    @model_validator(mode="before")
    @classmethod
    def validate_indices_or_abort(cls, data):
        try:
            sides = data.get("sides", [])
            active_side = data.get("active_side", 0)
            active_fighter_index = data.get("active_fighter_index", 0)

            if not sides:
                data["active_side"] = 0
                data["active_fighter_index"] = 0
                return data  # allow empty context

            if not (0 <= active_side < len(sides)):
                warnings.warn(
                    f"Invalid active_side={active_side} for {len(sides)} sides.",
                    stacklevel=2,
                )
                return None

            if active_fighter_index < 0:
                warnings.warn(
                    f"Invalid active_fighter_index={active_fighter_index}.",
                    stacklevel=2,
                )
                return None

            if active_fighter_index >= len(sides[active_side]):
                warnings.warn(
                    f"active_fighter_index={active_fighter_index} "
                    f"out of range for side {active_side}.",
                    stacklevel=2,
                )
                return None

        except Exception as e:
            warnings.warn(
                f"Failed to validate BattleContext input: {e}",
                stacklevel=2,
            )
            return None

        return data

    @model_validator(mode="after")
    def check_context(self):
        check("turn >= 0", turn=self.turn)
        check("0 <= active_side <= len(sides)-1", active_side=self.active_side, sides=self.sides)
        check("0 <= active_fighter_index <= side_size-1", active_fighter_index=self.active_fighter_index, side_size=len(self.sides[self.active_side]))
        check("len(sides) == max_side", sides=self.sides, max_side=MAX_SIDE) # must have two sides, could have more, but for now just two TODO support more sides (issue with the display logic)
        for c in self.event_queue:
            sig = inspect.signature(c)
            for param in sig.parameters.values():
                # If any parameter has no default and is not VAR_POSITIONAL or VAR_KEYWORD
                if (
                    param.default is inspect.Parameter.empty
                    and param.kind
                    not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                ):
                    raise ValueError(f"Event queue contains a callable with required parameters: {c}")
        return self
    
    @property
    def fighters(self) -> list[FighterVolatile]:
        return self.left_side + self.right_side
    @property
    def active_fighter(self) -> FighterVolatile:
        return self.sides[self.active_side][self.active_fighter_index]
    @property
    def left_side(self) -> list[FighterVolatile]:
        return self.sides[0]
    @property
    def right_side(self) -> list[FighterVolatile]:
        return self.sides[1]
    @property
    def sides_alive(self) -> list[bool]:
        return [self.is_any_fighter_alive(i) for i in range(len(self.sides))]
    def is_any_fighter_alive(self, side_index: int) -> bool:
        for fv in self.sides[side_index]:
            if fv.alive:
                return True
        return False
    def get_fighter_side(self, fighter: FighterVolatile) -> list[FighterVolatile]:
        for side, fighters in enumerate(self.sides):
            if fighter in fighters:
                return side
        raise ValueError(f"Fighter {fighter.base_id} not found in either side.")
    def get_next_logs(self) -> list[str]:
        next_logs = []
        while(self.log_stack):
            next_log = self.log_stack.pop(0)
            next_logs.append(next_log)
            self.log_history.append(next_log)
        return next_logs

    @classmethod
    def from_sides(
        cls,
        sides: list[list[str]],
        *,
        turn: int = 0,
        active_side: int = 0,
        active_fighter_index: int = 0,
        event_queue: list[Callable] | None = None,
        log: list[str] | None = None,
    ) -> BattleContext:
        built_sides: list[list[FighterVolatile]] = []

        for side in sides:
            fighters: list[FighterVolatile] = []
            for fid in side:
                fv = FighterVolatile(base_id=fid)
                if fv:
                    fighters.append(fv)
            built_sides.append(fighters)

        return cls(
            sides=built_sides,
            turn=turn,
            active_side=active_side,
            active_fighter_index=active_fighter_index,
            event_queue=event_queue or [],
            log=log or [],
        )

# ------------------------------
# Battle Schema
# ------------------------------

class Battle(ResolvableModel):
    id: str

    max_turns: RINT = MAX_TURN

    background_sprite: RSTR = "/backgrounds/default.png"
    music: Optional[RSTR] = None

    base_context: BattleContext = Field(default_factory=BattleContext)
    current_context: Optional[BattleContext] = None  # mutable, per-battle context

    def model_post_init(self, __context=None):
        check("max_turns >= 0", max_turns=self.max_turns)
        if self.current_context is None:
            self.current_context = copy.deepcopy(self.base_context)

    @property
    def is_battle_over(self) -> bool:
        if sum(self.current_context.sides_alive) <= 1:
            self.current_context.log_stack.append("All opponents defeated!")
            return True
        if self.current_context.turn >= self.max_turns:
            self.current_context.log_stack.append("Maximum turns reached!")
            return True
        return False

    @classmethod
    def from_sides(
        cls,
        id: str,
        sides: list[list[str]],
        *,
        max_turns: int = MAX_TURN,
        background_sprite: str | None = None,
        music: str | None = None,
    ) -> Battle:
        base_ctx = BattleContext.from_sides(sides)

        battle = cls(
            id=id,
            max_turns=max_turns,
            background_sprite=background_sprite or "/backgrounds/default.png",
            music=music,
            base_context=base_ctx,
        )

        battle.current_context = copy.deepcopy(base_ctx)
        return battle

# ------------------------------
# Battle Config
# ------------------------------

class BattleConfig(ResolvableModel):
    pass