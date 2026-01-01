from __future__ import annotations
from pydantic import Field, PrivateAttr, model_validator
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

    # Remove these as model fields; keep them purely as properties backed by private attrs
    # current_buffs: list[Buff] = None
    # current_status: list[Status] = None
    current_fighter: Optional[Fighter] = None  # mutable, per-battle fighter

    # Private backing fields
    _current_buffs: list[Buff] = PrivateAttr(default_factory=list)
    _current_status: list[Status] = PrivateAttr(default_factory=list)
    _buffed_max_stats: FighterStats | None = PrivateAttr(default=None)
    _base_max_stats: FighterStats | None = PrivateAttr(default=None)

    def model_post_init(self, __context=None):
        base = self.base_fighter
        if base is None:
            raise ValueError(f"FighterVolatile references unknown fighter id: {self.base_id}")

        # Preserve immutable base maxima
        self._base_max_stats = copy.deepcopy(base.stats)

        # Set up mutable current fighter/stats from starting_stats
        if self.current_fighter is None:
            self.current_fighter = copy.deepcopy(base)
            self.current_fighter.stats = copy.deepcopy(base.starting_stats)
        else:
            base_data = base.model_dump()
            override_data = self.current_fighter.model_dump()
            merged_data = {**base_data, **override_data}

            merged_stats = copy.deepcopy(base.starting_stats)
            if override_data.get("stats"):
                for k, v in override_data["stats"].model_dump().items():
                    merged_stats.__setattr__(k, v)
            merged_data["stats"] = merged_stats

            self.current_fighter = Fighter(**merged_data)

        # Merge buffs/status defaults
        base_buffs = copy.deepcopy(base.starting_buffs)
        base_status = copy.deepcopy(base.starting_status)
        self._current_buffs = list(base_buffs)
        self._current_status = list(base_status)

        self._recompute_buffs()

    @property
    def base_fighter(self) -> Optional[Fighter]:
        return registry.get("fighters").set.get(self.base_id, None)

    @property
    def alive(self) -> bool:
        return self.current_stats.hp > 0

    @property
    def has_shield(self) -> bool:
        return self.current_stats.shield > 0

    @property
    def current_stats(self) -> FighterStats:
        return self.current_fighter.stats

    @current_stats.setter
    def current_stats(self, new_stats: FighterStats):
        for k, v in new_stats.model_dump().items():
            setattr(self.current_fighter.stats, k, v)
        FighterStats.model_validate(self.current_fighter.stats)
        self._recompute_buffs()

    @property
    def computed_stats(self) -> FighterStats:
        if self._buffed_max_stats is None:
            self._recompute_buffs()
        return copy.deepcopy(self._buffed_max_stats)

    @property
    def current_buffs(self) -> list[Buff]:
        return self._current_buffs

    @current_buffs.setter
    def current_buffs(self, value: list[Buff]):
        self._current_buffs = list(value)
        if len(self._current_buffs) > MAX_BUFFS:
            warnings.warn(f"FighterVolatile '{self.base_id}' has more than {MAX_BUFFS} buffs; truncating.", stacklevel=2)
            self._current_buffs = self._current_buffs[:MAX_BUFFS]
        self._recompute_buffs()

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
    def current_status(self) -> list[Status]:
        return self._current_status

    @current_status.setter
    def current_status(self, value: list[Status]):
        self._current_status = list(value)

    def _calc_buffed_max(self) -> FighterStats:
        max_stats = copy.deepcopy(self._base_max_stats)
        for buff in self._current_buffs or []:
            if buff.stat in max_stats.model_fields:
                new_val = getattr(max_stats, buff.stat) + buff.amount
                setattr(max_stats, buff.stat, max(0, new_val))
        FighterStats.model_validate(max_stats)
        return max_stats

    def _rebalance_current_against_new_max(self, new_max: FighterStats):
        old_max = self._buffed_max_stats or copy.deepcopy(self._base_max_stats)
        for stat_name in new_max.model_fields:
            old_cap = getattr(old_max, stat_name)
            new_cap = getattr(new_max, stat_name)
            cur = getattr(self.current_stats, stat_name)

            if new_cap >= old_cap:
                if old_cap <= 0:
                    new_cur = min(cur, new_cap)
                else:
                    new_cur = round(cur * new_cap / old_cap)
            else:
                new_cur = min(cur, new_cap)

            new_cur = max(0, min(int(round(new_cur)), new_cap))
            setattr(self.current_stats, stat_name, new_cur)

    def _recompute_buffs(self):
        new_max = self._calc_buffed_max()
        self._rebalance_current_against_new_max(new_max)
        self._buffed_max_stats = copy.deepcopy(new_max)

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
    
    def tick_buffs(self, log_stack=None):
        """
        Decrement finite buffs by 1; remove those that reach 0.
        duration == -1 is infinite.
        """
        new_buffs = []
        expired = []
        for buff in self.current_buffs or []:
            # Infinite
            if buff.duration == -1:
                new_buffs.append(buff)
                continue
            # Finite: decrement
            buff = copy.deepcopy(buff)
            buff.duration = max(-1, buff.duration - 1)
            if buff.duration == 0:
                expired.append(buff)
                continue
            new_buffs.append(buff)

        # Reassign via setter to trigger rebalance
        self.current_buffs = new_buffs

        if log_stack is not None:
            for b in expired:
                log_stack.append(f"{self.current_fighter.name}'s {b.stat} buff expired")
    
    def add_stat(self, stat: str, amount: int | float) -> int:
        """
        Add to a stat on current_stats, clamped to [0, computed_stats.<stat>].
        Returns the actual amount applied (may be 0 if already at cap or amount <= 0).
        """
        amt = int(round(amount))
        if amt == 0:
            return 0
        if stat not in self.current_stats.model_fields:
            raise ValueError(f"Unknown stat '{stat}'")

        cap = getattr(self.computed_stats, stat)
        cap = max(0, int(round(cap)))
        before = getattr(self.current_stats, stat)

        new_val = before + amt
        new_val = max(0, min(new_val, cap))
        setattr(self.current_stats, stat, new_val)

        return new_val - before
    
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