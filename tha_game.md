### 🎮 **Game Overview**

* Local **2-player** battle (same keyboard or controller input).
* **Menu-driven** turn system (not real-time).
* Game flow:

  1. **Title screen** – “Start Game”, “Parameters”, “Credits”, “Quit”.
  2. **Character selection** – both players pick fighters, view stats & moves.
  3. **Battle screen** – turn-based combat using the move selection UI.
* Everything should be fully functional but visually simple (rectangles, text, bars).
* Include inline comments explaining structure and how to extend it.

---

### 🧱 **Project Structure**

Organize the code using clear classes or modules such as:

* `Game` – overall state management and transitions.
* `Menu` – title, parameters, and credits screens.
* `Character` – stores stats, current HP, charge, statuses.
* `BattleSystem` – manages turn order, damage, rolls, and effects.
* `MoveEffects` – handles status and buff logic.
* `UI` – draws health bars, charge bars, menus, and roll results.

All in a single Python file for the POC.

---

### 🧍‍♂️ **Characters & Configuration**

Use plain Python dictionaries (no JSON files) for configuration.

**Dictionaries:**

* `MOVES`: each entry has

  * `name`
  * `bp` (base power)
  * `function` (reference to effect function)
  * `desc` (string for UI)
  * `sound` (path or identifier string for move sound effect)
* `CHARACTERS`: each entry has

  * `name`
  * `stats` → `hp`, `attack`, `defense`, `charge_bonus`
  * `moveset` → list of standard moves
  * `charge_move` → one special move (always unique)

Provide at least **two sample characters** and **several example moves**, including:

* Basic damage move
* Buff/debuff move
* Status-inflicting move
* One charge move example

Characters use **256×256 alpha PNGs** (for later art replacement).
For now, draw colored rectangles as placeholders.

---

### ⚔️ **Battle System**

* Purely turn-based, menu-driven.
* Turn order:

  * Determined by a **coin flip** at the start of battle.
  * The player who goes second gets a small logical bonus (e.g., defense or charge boost).
* Moves can:

  * Deal damage using base power, attack, defense, and modifiers.
  * Apply buffs, debuffs, or statuses.
* Damage includes slight random variance (Pokémon-style).

---

### 🎲 **Attack Roll System**

* Each attack triggers an **attack roll** — a random integer 1-20 (like a D20).
* The roll result is **shown on screen** for both players.
* The roll controls outcome randomness, damage variance, and potential effects:

  * **1-5:** weak hit; possible self-debuff or miss.
  * **6-15:** normal hit.
  * **16-19:** strong hit (+damage or buff).
  * **20:** critical hit; may trigger a special status or bonus (like *javaBien*).
* The attack roll replaces flat RNG for damage variation.
* Certain statuses or effects can modify roll results or outcomes.
* Always display a short message/log of the roll and result on the battle screen.

---

### ⚡ **Charge System**

* Each character has a **charge bar** displayed below HP.
* The bar fills each turn; higher `charge_bonus` increases charge gain rate.
* When full, the player may use their **`charge_move`**, which consumes the entire bar.
* The bar and charge move logic should be implemented visibly and functionally.

---

### ☕ **Status Effects**

Implement the following as working examples:

| Status           | Effect                                                                                          |
| ---------------- | ----------------------------------------------------------------------------------------------- |
| **javaBien**     | Boosts the attack roll temporarily.                                                             |
| **javaPause**    | Prevents acting for a few turns (freeze-like).                                                  |
| **jeudiSoir**    | Big attack buff and attack-roll boost for X turns, then automatically applies **retour2Cuite**. |
| **retour2Cuite** | Permanent attack-roll debuff; cannot be removed.                                                |

Status effects can stack logically and expire after turn counters where appropriate.

---

### 🔉 **Audio**

Implement an audio management structure (via `pygame.mixer`) but leave all sounds **muted or commented out** by default.
Reference filenames so users can replace them later:

* `title_theme.mp3`
* `battle_theme.mp3`
  Each move in `MOVES` also includes a `sound` property reference.

---

### ⚙️ **Parameters Menu**

In-game “Parameters” should allow:

* Adjusting **volume**
* Toggling **fullscreen**
* Muting/unmuting audio
  (Changing characters is **not** allowed in-game.)

Settings don’t need to persist between runs in the POC.

---

### 🧩 **Technical Requirements**

* Use **pygame** for display, event handling, and animation loops.
* Show placeholder sprites as rectangles (with idle/attack frame toggles).
* Use modular functions and clear comments to explain where to expand features.
* Demonstrate:

  * Buff/debuff logic
  * Status effects
  * Charge mechanics
  * Attack roll results
  * Menu flow