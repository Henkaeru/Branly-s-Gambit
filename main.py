import random
from time import sleep
from core.registry import registry
from systems.battle.engine import BattleMode
from systems.battle.schema import Battle, FighterVolatile
from systems.display.engine import DisplayEngine

import systems.moves
import systems.fighters
import systems.battle
import systems.display

# Optional: deterministic runs for debugging
random.seed(0)

def coerce_seq(val):
    """Return a list from val, or [] if it's None/invalid (incl. property objects)."""
    if val is None:
        return []
    if isinstance(val, property):
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    return []

def fmt_buffs(fv: FighterVolatile) -> str:
    buffs = coerce_seq(getattr(fv, "current_buffs", None))
    if not buffs:
        return "none"
    return ", ".join(f"{b.stat}{'+' if b.amount >= 0 else ''}{b.amount}" for b in buffs)

def fmt_statuses(fv: FighterVolatile) -> str:
    statuses = coerce_seq(getattr(fv, "current_status", None))
    if not statuses:
        return "none"
    return ", ".join(s.id for s in statuses)

def fmt_moves(fv: FighterVolatile) -> str:
    moves = getattr(fv.current_fighter, "moves", []) or []
    return ", ".join(moves) if moves else "none"

def fmt_fighter(fv: FighterVolatile) -> str:
    cs = fv.current_stats          # current (mutable) stats
    ms = fv.computed_stats         # buffed maxima (base + buffs)
    return (
        f"{fv.current_fighter.name:>12} | "
        f"HP {cs.hp:>3}/{ms.hp:<3} | "
        f"SH {cs.shield:>3}/{ms.shield:<3} | "
        f"AT {cs.attack:>3}/{ms.attack:<3} | "
        f"DE {cs.defense:>3}/{ms.defense:<3} | "
        f"CH {cs.charge:>3}/{ms.charge:<3} | "
        f"Buffs: {fmt_buffs(fv)} | "
        f"Status: {fmt_statuses(fv)} | "
        f"Moves: {fmt_moves(fv)}"
    )

def print_state(prefix: str, battle_engine):
    ctx = battle_engine.battle.current_context
    left = ctx.sides[0]
    right = ctx.sides[1]
    print(prefix)
    print(f"  Turn: {ctx.turn} | Active side: {ctx.active_side} | Active fighter idx: {ctx.active_fighter_index}")
    for fv in left:
        print(f"  L {fmt_fighter(fv)}")
    for fv in right:
        print(f"  R {fmt_fighter(fv)}")

def print_logs(prefix: str, logs: list[str]):
    for log in logs:
        print(f"{prefix}{log}")

def main():
    display_engine = registry.get("display")
    display_engine.run()

if __name__ == "__main__":
    main()