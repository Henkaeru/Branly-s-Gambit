# Branly's Gambit

*A local 2-player turn-based fighting game prototype inspired by Pokémon battles, built with Python and Pygame.*

---

## Overview

**Branly's Gambit** is a **proof of concept (POC)** demonstrating the structure, combat flow, and menu system for a local turn-based fighting game.  
The prototype focuses on **clarity, modularity, and extensibility** rather than visuals — designed to serve as a foundation for a future playable demo.

Players battle using characters with unique stats, moves, and charge-based special attacks.  
Combat is **menu-driven** and **turn-based**, with RPG-inspired mechanics such as rolls, buffs, debuffs, and statuses.

---

## Project Structure

The POC is implemented in a **single file (`main.py`)** for simplicity but organized into modular classes:

| Class | Description |
|-------|--------------|
| **`Game`** | Manages overall state, menus, and scene transitions. |
| **`Menu`** | Handles title screen, parameters, and credits. |
| **`Character`** | Stores fighter data: HP, attack, defense, charge, and statuses. |
| **`BattleSystem`** | Manages turns, move logic, damage rolls, and effects. |
| **`MoveEffects`** | Contains buff, debuff, and status effect logic. |
| **`UI`** | Draws menus, health bars, charge bars, and combat logs. |

All assets (sprites, sounds, etc.) are represented as placeholders (rectangles, text, and muted audio) for now.

---

## Game Flow

1. **Title Screen**
   - Start Game  
   - Parameters  
   - Credits  
   - Quit  

2. **Character Selection**
   - Both players pick from a list of characters.
   - Each character displays stats and move descriptions.

3. **Battle**
   - Players take turns choosing moves.
   - Each move triggers a **D20 roll** determining the outcome (miss, normal, critical, etc.).
   - Charge builds every turn, enabling powerful *Charge Moves*.
   - Statuses and buffs dynamically affect combat performance.

---

## Combat Mechanics

### Attack Roll
Every attack performs a **D20 roll**:
| Roll | Result |
|------|---------|
| 1–5  | Weak hit / possible self-debuff |
| 6–15 | Normal hit |
| 16–19| Strong hit (+damage or buff) |
| 20   | Critical hit with special bonus |

The roll result and commentary are displayed on-screen.

### Charge System
- Each turn adds charge points.
- When full, the **Charge Move** becomes available.
- Using it consumes the entire charge bar.

### Status Effects
| Status | Description |
|---------|-------------|
| **javaBien** | Temporarily boosts attack rolls. |
| **javaPause** | Prevents action for a few turns (freeze-like). |
| **jeudiSoir** | Big temporary buff, followed by **retour2Cuite**. |
| **retour2Cuite** | Permanent attack-roll debuff. |

---

## Example Content

### Characters
Two example characters are included for demonstration:
- **Aether**
- **Bront**

### Moves
Includes sample move types:
- Basic damage attack  
- Buff/debuff moves  
- Status-inflicting attack  
- One unique charge move per character  

All moves are defined via simple Python dictionaries, e.g.:

```python
MOVES = {
    "basic_strike": {
        "name": "Basic Strike",
        "bp": 30,
        "function": MoveEffects.basic_damage,
        "desc": "A simple physical hit.",
        "sound": "strike.wav"
    }
}
```
---

## Parameters Menu

Accessible from the title screen:

* Adjust **volume**
* Toggle **fullscreen**
* Mute/unmute audio

(Changes are temporary for this POC.)

---

## Audio System

The structure for sound playback is implemented using `pygame.mixer`, but all sounds are **muted by default**.

**Reference files:**

* `title_theme.mp3`
* `battle_theme.mp3`
* Move-specific sounds (`strike.wav`, `buff.wav`, etc.)

You can replace these with your own `.mp3` or `.wav` files later.

---

## Tech Stack

* **Language:** Python 3
* **Library:** [pygame](https://www.pygame.org/)
* **Dependencies:** None beyond `pygame`

---

## How to Run

1. Install dependencies:

   ```bash
   pip install pygame
   ```

2. Run the prototype:

   ```bash
   python main.py
   ```

3. Navigate menus with **arrow keys** and confirm with **Enter**.

---

## Next Steps / Expansion Ideas

* Add sprite and animation support
* Expand move and status effect systems
* Add saveable settings
* Implement AI for single-player mode
* Add network/local co-op layer
* Improve UI/UX with animations and icons
* Integrate particle and sound effects

---

## License

This prototype is provided for educational and demonstration purposes.

---

## Credits

**Branly’s Gambit**
Prototype by *Keren Courtois*
Concept & design inspired by classic turn-based RPGs like *Pokémon* and *Eternal Sonata*.
