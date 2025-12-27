# Move Configuration System (v2.2)

**Version:** 2.2
**Purpose:** Declarative JSON moves with randomization, context propagation, and type-based damage/buff modifiers.

---

## Table of contents

1. [Overview](#overview)
2. [Core concepts](#core-concepts)
3. [Field reference table](#field-reference-table)
4. [Top-level move schema](#top-level-move-schema)
5. [Action object format & rules](#action-object-format--rules)
6. [Action function reference](#action-function-reference)
7. [Random number & string DSL](#random-number--string-dsl)
8. [Examples](#examples)
9. [Notes & tips](#notes--tips)

---

## Overview

Moves are JSON objects with a **context** and a list of **actions**. Context defines parameters like `amount`, `chance`, `target`, and arithmetic modifiers (`multiply`, `add`).

* Actions inherit merged context unless explicitly overridden.
* Nested actions (`random`, `repeat`, `condition`) receive the merged context automatically.
* Move `type` and `target` interactions affect **damage and buff formulas** (see below).

---

## Core concepts

### Context propagation

* Merges top-down from move → action → nested objects.
* Local overrides apply only to the action where defined.
* All nested objects (`status`, `condition`, `repeat`, `random`) inherit context automatically.

### Arithmetic evaluation

```
effective_amount = (amount * multiply) + add
```

* `amount` float → fraction (percentage) of `calc_target.calc_field`.
* `amount` int → flat value.

### Dual target model

| Field         | Meaning                                               |
| ------------- | ----------------------------------------------------- |
| `target`      | Entity receiving the effect                           |
| `calc_target` | Entity used as numeric basis (stats, % calculations)  |
| `calc_field`  | Attribute of `calc_target` (e.g., `"hp"`, `"attack"`) |

### Move type interaction

* Each move has a `type` (e.g., `"dev"`, `"opti"`, etc.).
* **Self-type bonus:** If move type matches `self.type`, damage/buff multiplied by 1.1.
* **Effectiveness modifier:** Depends on move type vs target type → multiplier `[0,1.5]`.
* Any type of move follow this rule (damage, heal, shield, buff)
* Target self follow same rule, e.g.
I use a super-effective move on myself (even heal or buff)

---

## Field reference table

| Field        | Type               | Default                      | Domain / Limits                                     | Scope         | Notes                                        |
| ------------ | ------------------ | ---------------------------- | --------------------------------------------------- | ------------- | -------------------------------------------- |
| id           | string             | required                     | min_length=3, max_length=63                         | Move / Action | Must be unique move id                       |
| name         | RSTR               | `"unknown"`                  | 1–127 chars                                         | Move          | Human-readable name                          |
| description  | RSTR               | `"No description provided."` | 0–511 chars                                         | Move          | Optional                                     |
| enabled      | bool               | True                         | —                                                   | Move          | Disable/enable move                          |
| type         | RSTR               | `"none"`                     | `["dev","opti","syst","data","proj","team","none"]` | Move          | Used in self-type/effectiveness calculations |
| category     | RSTR               | `"none"`                     | `["damage","support","special","none"]`             | Move          | For classification                           |
| charge_usage | RNUM               | 0.0                          | 0.0–1.0                                             | Move          | Fraction of charge consumed                  |
| amount       | RNUM               | 0                            | int ≥0 / float ≥0                                   | Global        | Flat if int, % if float                      |
| chance       | RNUM               | 1.0                          | 0.0–1.0                                             | Global        | Probability move/action executes             |
| target       | RSTR               | `"opponent"`                 | `["self","opponent"]`                               | Global        | Receives effect                              |
| calc_target  | RSTR               | `"self"`                     | `["self","opponent"]`                               | Global        | Basis for calculations                       |
| calc_field   | RSTR               | `"hp"`                       | Stat keys (attack, defense, hp, charge_bonus)       | Global        | Used for % calculations                      |
| multiply     | RNUM               | 1.0                          | ≥0                                                  | Global        | Multiplies amount first                      |
| add          | RNUM               | 0                            | any                                                 | Global        | Adds after multiply                          |
| flat         | RNUM               | 0                            | any                                                 | Global        | Flat additive override                       |
| duration     | RINT               | -1                           | ≥-1                                                 | Global        | -1 = infinite                                |
| sound        | RSTR               | null                         | path exists                                         | Move          | Optional audio file                          |
| actions      | list[Action]       | []                           | —                                                   | Move          | Ordered list of actions                      |
| crit_chance  | RNUM               | 0.0                          | 0.0–1.0                                             | Damage        | Chance for critical hit                      |
| crit_damage  | RNUM               | 0                            | ≥0                                                  | Damage        | Extra damage applied on crit                 |
| piercing     | RNUM               | 0.0                          | 0.0–1.0                                             | Damage        | Fraction of defense ignored                  |
| stat         | RSTR / list[RSTR]  | `"attack"`                   | Stat keys                                           | Buff          | Stats to buff/debuff                         |
| field        | RSTR               | required                     | dot-path                                            | Modify        | Attribute to modify                          |
| value        | RVAL               | required                     | any                                                 | Modify        | New value for field                          |
| text         | RSTR               | required                     | 0–511 chars                                         | Text          | Message for UI/log                           |
| style        | RSTR               | `"{}"`                       | parseable dict                                      | Text          | color ∈ COLOR, flags ∈ STYLE                 |
| operation    | RSTR               | `"add"`                      | `["add","remove"]`                                  | Status        | Add/remove status                            |
| status       | list[Status]       | required                     | Status IDs                                          | Status        | Status objects                               |
| conditions   | list[Condition]    | required                     | Condition IDs                                       | Condition     | Must pass before actions                     |
| choices      | list[RandomChoice] | required                     | weight ≥0                                           | Random        | Probabilistic selection                      |
| count        | RINT               | required for repeat          | ≥0                                                  | Repeat        | Times to repeat                              |
| unique       | bool               | optional                     | —                                                   | Random        | Without replacement if true                  |

---

## Action function reference

### `damage`

* **Params:** `crit_chance`, `crit_damage`, `piercing`
* **Behavior:** Apply `amount` to target.

  * Percent amount → `calc_target.calc_field`.
  * Flat amount → direct.
* **Tips:**

  * Criticals are based on `crit_chance` and apply `crit_damage`
  * Piercing reduces defense fractionally
  * `crit_damage` is applied after multiply and add

---

### `buff`

* **Params:** `stat` (string or list)
* **Behavior:** Apply temporary stat modifiers.
* **Tips:**

  * Buffs are additive, not multiplicative
  * Negative `amount` -> debuff
  * Max 4 buffs per entity
  * `+10% "attack"`, `+10 "attack"`, `-5% "defense"` makes 3 buffs
  * Uses `amount`, `duration`, `calc_target`

---

### `status`

* **Params:** `operation`, `status` list
* **Behavior:** Add/remove statuses

---

### `shield`

* **Params:** None
* **Behavior:** Creates protective barrier
* **Tips:** Uses `amount`, `duration`, `calc_target`

---

### `heal`

* **Params:** None
* **Behavior:** Restore HP using `amount`
* **Tips:** 

  * Uses `amount`, `calc_target`

---

### `modify`

* **Params:** `field`, `value`
* **Behavior:** Arbitrary attribute modification
* **Tips:** `"default"` reverts attribute

---

### `condition`

* **Params:** `conditions`, `actions`
* **Behavior:** Executes actions if all conditions pass

---

### `random`

* **Params:** `choices`, optional `count`, optional `unique`
* **Behavior:** Randomly selects actions, can use weights

---

### `repeat`

* **Params:** `actions`, `count`
* **Behavior:** Repeat actions sequentially

---

### `text`

* **Params:** `text`, `style`
* **Behavior:** Write log/UI text
* **Tips:** 

  * Tokens e.g. `{self.move[0].id}` replaced with merged context
  * style parsed as dict

---

## Random number & string DSL

* `RNUM`, `RINT`, `RSTR` support:

```
r[min,max] → random float
l[...] → pick recursively from list
wl[(value,weight),...] → weighted choice
```

* Strings and lists are recursive.
* Invalid syntax raises exception.

---

## Examples

**Flat attack, type bonus**

```json
{ 
    "id": "slash", 
    "type": "dev", 
    "amount": 40, 
    "actions":[
        {"id":"damage"}
    ] 
}
```

**Random multi-choice**

```json
{ 
    "id": "chaos_strike", 
    "actions":[{
        "id":"random",
        "choices":[
            {"action":{"id":"damage"},"weight":3},
            {"action":{"id":"heal","calc_target":"opponent"},"weight":1}
        ]
    }]
}
```