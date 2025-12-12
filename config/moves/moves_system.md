# Move Configuration System (v1.3 — revised)

**Version:** 1.3 (revised)
**Purpose:** Fully declarative JSON moves that the engine loads and executes.

---

## Table of contents

1. [Overview](#overview)
2. [Core concepts](#core-concepts)

   * [Context propagation](#context-propagation)
   * [Arithmetic evaluation (PEMDAS)](#arithmetic-evaluation-pemdas)
   * [Dual target model](#dual-target-model)
3. [Top-level move schema](#top-level-move-schema)
4. [Action object format & rules](#action-object-format--rules)
5. [Action function reference](#action-function-reference)

   * [attack](#attack)
   * [buff](#buff)
   * [status](#status)
   * [shield](#shield)
   * [heal](#heal)
   * [modify](#modify)
   * [condition](#condition)
   * [random](#random)
   * [repeat](#repeat)
   * [text](#text)
6. [Type system (6 + 1 dummy)](#type-system-6--1-dummy)
7. [Examples](#examples)
8. [Notes & implementation tips](#notes--implementation-tips)

---

## Overview

Moves are fully data-driven JSON definitions. Each move contains general parameters (context) and an ordered list of `actions`. Actions inherit the merged move context and may override any general parameter. All nested object receive the merged context automatically.

This document describes the canonical schema, defaults, and semantics for all fields and actions.

---

## Core concepts

### Context propagation

The engine merges context progressively and **passes the merged context recursively** to every nested object (action, condition, random choice, repeat, or status). That means a `duration`, `amount`, or `calc_target` defined at the move level is automatically available to all child elements unless explicitly overridden.

### Arithmetic evaluation (PEMDAS)

Numeric transforms to `amount` are applied in PEMDAS order (as applied to the DSL fields available):

```python
// flat amount
effective_amount = (((amount * multiply) / divide) + add) - subtract
// percent amount
effective_amount = ((((calc_target.calc_field * amount) * multiply) / divide) + add) - subtract
```

* `amount`: int -> flat; float -> percent (0.25 = 25%).
* `multiply` / `divide` / `add` / `subtract` follow the order above.
* After the arithmetic pipeline, action-specific modifiers (e.g. `crit_damage`) may be applied as specified by the action.

### Dual target model

* `target` — the entity that **receives** the effect
* `calc_target` — the entity used for **calculations** (stats, % basis, etc.). Default: `"self"`.
* `calc_field` — the field of the calc_target used. Default: `"hp"`.

Examples:

* Deal 20% of **your HP** to opponent -> `target: "opponent"`, `calc_target: "self"`, `calc_field: "hp"`, `amount: 0.2`.
* Deal damage based on **opponent's attack** to that same opponent -> `target: "opponent"`, `calc_target: "opponent"`, `calc_field: "attack"`.

---

## Top-level move schema

> All fields that have defaults are optional in JSON. Fields without defaults are required (or must be inherited from context).

```json
{
  "id": "string",                 // required
  "name": "string",               // default: "unknown"
  "enabled": true,                // default: true
  "type": "string",               // default: "none"
  "category": "string",           // default: "none"
  "charge_usage": 0.1,            // default: 0.0 (1.0 if category: "special")
  "amount": 0,                    // default: 0 (int or float)
  "chance": 1.0,                  // default: 1.0 (0.0 - 1.0)
  "target": "self" / "opponent",  // default: "opponent"
  "calc_target": "self",          // default: "self"
  "calc_field": "string",         // default: "hp"
  "multiply": 1.0,                // default: 1.0
  "divide": 1.0,                  // default: 1.0
  "add": 0,                       // default: 0
  "subtract": 0,                  // default: 0
  "duration": -1,                 // default: -1 (infinite)
  "sound": "string",              // default: null
  "description": "string",        // default: ""
  "actions": [ ... ]              // required (or an empty list)
}
```

**Notes**

* `charge_usage` percentage of charge depleted when using a move (can't use the move without enough charge). Default to 1.0 for `special` moves.
* `amount` default is `0`. If `amount` is a float it is interpreted as a percentage relative to `calc_target.calc_field` (see `calc_target`). `1.0` = 100% of the chosen basis.
* `chance` is always in the range `0.0`–`1.0`. At move level it is the probability the whole action sequence runs. Inside an action it is the chance that specific action executes (after the move triggered).
* `duration` default `-1` means indefinite/permanent.

---

## Action object format & rules

Each action is an object with:

```json
{
  "id": "string",        // action function identifier (required)
  ...,                   // action-specific params (optional or required depending on action)
}
```

* Actions inherit the full merged context from the parent move. Any field may be overridden by placing that general field at the action level (e.g. overriding `amount`, `calc_target`, `target`, `chance`, arithmetic modifiers, etc.).
* When an action executes, the engine computes the `effective_amount` by applying PEMDAS to the `amount` value that results from merging (move-level + action-level overrides).
* Action functions receive the full merged context (including all general fields).

---

## Action function reference

> Defaults listed where applicable. The general move fields (`amount`, `chance`, `target`, `calc_target`, `calc_field`, `multiply`, `divide`, `add`, `subtract`, `duration`, `description`) are available to all action (they may however not be relevent to some action).

---

### `damage`

Deals damage to `target` using the merged `amount` and arithmetic pipeline.

**params (all optional)**

* `crit_chance` (float, default `0.0`) — chance to land a critical hit (0–1).
* `crit_damage` (int | float, default `0`) — extra damage applied on critical; int = flat, float = percent.
* `piercing` (float, default `0.0`) — fraction (0–1) of target defense ignored.

**Behavior notes**

* `crit_damage` is applied on a crit roll determined by `crit_chance`.
* `piercing` reduces the defensive value used in damage computation by that fraction.

---

### `buff`

Applies a temporary positive modifier to base stat(s)


**params (required)**

* `stat` (string or list) — one or multiple stats: `"attack"`, `"defense"`, `"hp"`, `"charge_bonus"`.
* `max_stack` (int, default `-1`) — maximum stacks; `-1` means infinite.

**Usage**

* Uses the general `amount` to determine the magnitude (flat if int, percent if float). For debuff use negative `amount`.
* Uses `duration` general field (default `-1`) for application length.

**Behavior notes**

* Buff are additive not multiplicative. A stat buffed by 50%, and then buffed by another 50% equals a buff of 100%.

---

### `status`

Adds or removes statuses (status objects are modular and receive the general context).

**params (required)**

* `operation`: `"add"` | `"remove"`
* `status`: list of status objects to add/remove: `{ "id": "poison", ... }`

**Behavior**

* The general move context (e.g., `duration`, `chance`, `calc_target`) is passed down to each status entry automatically. Individual status objects may also include their own params.

---

### `shield`

Creates a damage-absorbing barrier (a "shield").

* Uses general fields `amount` (flat or percent of `calc_target.calc_field`), `duration`, `target`, `calc_target`, `calc_field`.
* No extra `params` required by default.

---

### `heal`

Restores HP to `target`.

* Uses general fields `amount`, `calc_target`, etc. No extra `params` required by default.

---

### `modify`

Modifies arbitrary attributes on the chosen entity (or reverts to default).

**params (required)**

* `field` (string) — dot-path to the attribute (e.g., `"stats.attack"`, `"sprite"`, `"moves.2.id"`).
* `value` (any) — new value to set. Use the string `"default"` to revert to base/default value.

---

### `condition`

Conditionally executes actions if all conditions pass.

**params (required)**

* `conditions`: list of condition objects: `{ "id": "hp_below", ... }`
* `actions`: list of action objects to execute if all conditions return true.

**Behavior**

* Conditions receive the full merged context.
* The `actions` block inherits and receives the context as well.

---

### `random`

Randomly selects actions to trigger.

**params (required)**

* `choices`: list of `{ "action": <action_object>, "weight": int }` — the possible choices.
* `count` (int, default `1`) — how many choices to execute.
* `unique` (bool, default `false`) — when `true`, prevents choosing the same choice more than once within this random call.

**Behavior**

* Each chosen `action` receives the same parent merged context (unless the action itself overrides specific fields).
* `choices` weights are used for probabilistic selection. And defaults to 1.

---

### `repeat`

Repeats the given actions N times.

**params (required)**

* `count` may be:

  * an `int` (e.g., `3`),
  * a 2-tuple `(min, max)` representing an inclusive range (engine selects a random integer in range),
  * a list of integers (e.g., `[1,3,4,7]`), or
  * a weighted list `[(value, weight), ...]` where engine selects according to the weights.
* `actions` — list of action objects to repeat.

**Behavior**

* Each repetition receives the merged context. Repetitions are sequential; results of previous repetitions are visible to next ones.

---

### `text`

Writes a line to the battle log / UI text box.

**params (required)**

* `text` (string) — message template with tokens for each parameter of the context like `{self}`, `{opponent}`, `{move.id}`, `{move.name}`, `{self.moves[2].amount}`.
* `style` (string or dict, default `"default"`) — style ID or inline style object (e.g., `{ "color": "red", "bold": true }`).

---

## Type system (6 + 1 dummy)

The `"type"` field takes one of the following IDs. These are used for type interactions.

* `dev`  — Réaliser un développement d’application
* `opti`  — Optimiser des applications informatiques
* `syst`— Administrer des systèmes informatiques communicants complexes
* `data` — Gérer des données de l’information
* `proj` — Conduire un projet
* `team` — Travailler dans une équipe informatique
* `none` — Neutral / dummy (no special interactions)

---

## Examples

### Simple flat-amount attack (uses attacker stats)

```json
{
    "id": "flat_slash",
    "amount": 40,
    "calc_field": "attack", // not required as attack action default override with "attack"
    "name": "Flat Slash", // not required
    "enabled": true, // not required
    "type": "dev", // not required
    "category": "damage", // not required
    "chance": 1.0, // not required
    "target": "opponent", // not required
    "calc_target": "self", // not required
    "description": "A simple 40-ish flat attack.", // not required
    "actions": [
        {
            "id": "attack",
            "crit_chance": 0.1, 
            "crit_damage": 10
        }
    ]
}
```

### Percent-of-self-HP attack with add/subtract/multiply/divide (PEMDAS)

```json
{
    "id": "hp_blast",
    "amount": 0.2,
    "add": 0.05,
    "multiply": 1.5,
    "calc_field": "hp", // required as attack action default override with "attack", could be set in the attack action directly.
    "name": "HP Blast", // not required
    "enabled": true, // not required
    "type": "dev", // not required
    "category": "damage", // not required
    "subtract": 0, // not required
    "divide": 1, // not required
    "chance": 1.0, // not required
    "target": "opponent", // not required
    "calc_target": "self", // not required
    "description": "Blast equal to 20% of your HP, multiplied by 1.5, +5% of your HP", // not required
    "actions": [ { "id": "attack" } ]
}
```

### Multi-hit with per-action override (first hit uses amount override)

```json
{
    "id": "triple_slash",
    "amount": 20,
    "calc_field": "attack", // not required as attack action default override with "attack"
    "name": "Triple Slash", // not required
    "type": "dev", // not required
    "category": "damage", // not required
    "chance": 1.0, // not required
    "target": "opponent", // not required
    "calc_target": "self", // not required
    "description": "Three hits; first hit is weak, others use base amount.", // not required
    "actions": [
        { 
            "id": "attack", 
            "amount": 10
        },
        { "id": "attack" },
        { "id": "attack" }
    ]
}
```

### Status add with inherited duration and chance

```json
{
    "id": "poison_cloud",
    "chance": 0.9,
    "duration": 3,
    "calc_target": "opponent", // required as poison amount would be based on self.hp otherwise.
    "name": "Poison Cloud", // not required
    "type": "admin", // not required
    "category": "support", // not required
    "amount": 0, // not required
    "target": "opponent", // not required
    "calc_field": "hp", // not required
    "description": "deal 5% of opponent hp to opponent each turn", // not required
    "actions": [
        {
            "id": "status",
            "operation": "add",
            "status": [
                { 
                    "id": "poison", 
                    "amount": 0.05 
                }
            ]
        }
    ]
}
```

### Random with repeating allowed (unique=false)

```json
{
    "id": "chaos_strike",
    "amount": 10,
    "target": "opponent", // not required
    "description": "1/4 to heal opponent, 3/4 to damage him", // not required
    "actions": [
        {
        "id": "random",
            "choices": [
                { "action": { "id": "attack" }, "weight": 3 },
                { 
                    "action": { 
                        "id": "heal", 
                        "calc_target": "opponent" // required as it would otherwise heal opponent based on self.hp
                    }, 
                    "weight": 1 // not required
                }
            ],
            "count": 10,
            "unique": false // not required
        }
    ]
}
```

---

## Notes & implementation tips

* **Defaults:** Implement default defaults as listed in the top-level schema (e.g. `amount=0`, `chance=1.0`, `multiply=1.0`, `duration=-1`, `type="none"`, `category="none"`).
* **PEMDAS:** Implement arithmetic transforms strictly in the order: `multiply`, `divide`, then `add`, then `subtract`.
* **Percent interpretation:** Any numeric field that is a Python/JSON float should be interpreted as a fraction (e.g., `0.25 = 25%`). For `amount` and other fields, if `amount` is `0.25` and `calc_target` is `"self"`, compute 25% of the chosen field (`calc_field`) from the `self` entity.
* **Context propagation:** The loader merges context top-down; every nested structure receives the merged dictionary. For example, a `condition` receives the move context, and the `condition`'s `actions` receive the same context with any condition-level overrides applied.
* **Action `params` requirement:** Some actions require `params` (e.g., `status` requires `operation` and `status` list; `modify` requires `field` and `value`); make sure action schemas declare `params` required or optional accordingly.
* **Random `count` semantics:** `count` specifies how many choice selections to perform. If `unique=true`, selections are without replacement up to the number of choices. If `unique=false`, choices may repeat. Use `weights` for selection probabilities.
* **Repeat `count` semantics:** Accept an integer, an inclusive range `(min,max)`, a list of candidates, or a weighted list of `(value, weight)` tuples. There is **no default** for `count` — the parameter is required for `repeat`.
* **Text styling:** You may store predefined style IDs (e.g., `"highlight"`, `"error"`) and/or accept inline style objects. Decide on a small style taxonomy for UI consumption.
