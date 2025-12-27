# main.py
"""
POC: Local 2-player turn-based fighting game (pygame)
- Single file prototype demonstrating:
  Game, Menu, Character, BattleSystem, MoveEffects, UI
- Use arrow keys / Enter / Esc to navigate menus and battle.
- Expand by replacing placeholders (rectangles) with 256x256 PNGs and adding sounds.
"""

import pygame
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

pygame.init()
pygame.mixer.init()  # we will not play sounds by default (muted/commented)

# ----------------------------
# Config / Constants
# ----------------------------
SCREEN_SIZE = (960, 640)
FONT = pygame.font.SysFont("consolas", 18)
BIGFONT = pygame.font.SysFont("consolas", 36)
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
GREY = (180, 180, 180)
RED = (200, 40, 40)
GREEN = (40, 200, 40)
BLUE = (60, 140, 200)
YELLOW = (240, 220, 80)
ORANGE = (230, 130, 40)
DARK = (30, 30, 30)

# ----------------------------
# Helper and Type Aliases
# ----------------------------
RollResult = Tuple[int, str]  # (d20 roll, category string)

# ----------------------------
# MOVES and CHARACTERS (configs)
# Moves reference functions in MoveEffects class (assigned later)
# ----------------------------
MOVES = {
    "Tackle": {
        "name": "Tackle",
        "bp": 40,
        "function": "basic_damage",
        "desc": "A standard physical attack.",
        "sound": "tackle.wav",
    },
    "FocusStrike": {
        "name": "Focus Strike",
        "bp": 55,
        "function": "basic_damage",
        "desc": "Strong attack with small variance.",
        "sound": "focus_strike.wav",
    },
    "Rally": {
        "name": "Rally",
        "bp": 0,
        "function": "buff_attack",
        "desc": "Boost own attack for 3 turns.",
        "sound": "rally.wav",
    },
    "StunShot": {
        "name": "Stun Shot",
        "bp": 20,
        "function": "inflict_status",
        "desc": "Low damage + chance to javaPause (stun).",
        "sound": "stun_shot.wav",
    },
    "ChargeBurst": {
        "name": "Charge Burst",
        "bp": 120,
        "function": "charge_move",
        "desc": "Powerful charge move that consumes full charge.",
        "sound": "charge_burst.wav",
    },
    "JeudiBlast": {
        "name": "Jeudi Blast",
        "bp": 90,
        "function": "jeudiSoir_move",
        "desc": "Big buff + roll boost, but later applies retour2Cuite.",
        "sound": "jeudi_blast.wav",
    },
}

CHARACTERS = {
    "Aether": {
        "name": "Aether",
        "stats": {"hp": 220, "attack": 50, "defense": 40, "charge_bonus": 1.0},
        "moveset": ["Tackle", "Rally", "StunShot"],
        "charge_move": "ChargeBurst",
    },
    "Bront": {
        "name": "Bront",
        "stats": {"hp": 240, "attack": 45, "defense": 48, "charge_bonus": 1.2},
        "moveset": ["FocusStrike", "Rally", "StunShot"],
        "charge_move": "JeudiBlast",
    },
}

# Placeholder paths (commented/inactive)
TITLE_THEME = "title_theme.mp3"
BATTLE_THEME = "battle_theme.mp3"

# ----------------------------
# Data classes
# ----------------------------
@dataclass
class Status:
    name: str
    turns_left: Optional[int]  # None for permanent (like retour2Cuite)
    # Effect parameters can be extended.
    magnitude: int = 0


@dataclass
class Character:
    config_key: str
    name: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    charge_bonus: float
    moveset: List[str]
    charge_move: str
    charge: float = 0.0
    statuses: Dict[str, Status] = field(default_factory=dict)
    # visual placeholder: rectangle color
    color: Tuple[int, int, int] = (100, 100, 255)
    sprite_path: Optional[str] = None  # for future replacement

    def is_alive(self) -> bool:
        return self.hp > 0

    def add_status(self, status_name: str, turns: Optional[int], magnitude: int = 0):
        """Add or refresh a status effect."""
        self.statuses[status_name] = Status(status_name, turns, magnitude)

    def remove_status(self, status_name: str):
        if status_name in self.statuses:
            del self.statuses[status_name]

    def get_roll_modifier(self) -> int:
        """Calculate modifiers to d20 roll from statuses."""
        mod = 0
        # javaBien: temporary boost
        if "javaBien" in self.statuses:
            mod += 3
        if "jeudiSoir" in self.statuses:
            mod += 4
        if "retour2Cuite" in self.statuses:
            mod -= 2
        return mod

    def tick_statuses(self):
        """Decrease duration counters, apply expiry side-effects if needed."""
        to_remove = []
        for sname, s in list(self.statuses.items()):
            if s.turns_left is not None:
                s.turns_left -= 1
                if s.turns_left <= 0:
                    # handle expiry logic
                    if sname == "jeudiSoir":
                        # upon expiry, apply permanent retour2Cuite
                        self.add_status("retour2Cuite", None)
                    to_remove.append(sname)
        for s in to_remove:
            if s in self.statuses:
                del self.statuses[s]

# ----------------------------
# Move Effects - implemented as functions referenced in MOVES by name
# ----------------------------
class MoveEffects:
    """
    Collection of move effect implementations. Each function receives:
    - user: Character performing move
    - target: Character receiving effect
    - bp: base power
    - context: BattleSystem to manipulate global flow (e.g., logs)
    """

    @staticmethod
    def basic_damage(user: Character, target: Character, bp: int, context: "BattleSystem", roll: RollResult):
        """Apply damage using attack/defense, with roll-based multiplier."""
        roll_value, category = roll
        # base damage formula: (bp * (user.attack/target.defense)) with modifiers
        base = bp * (user.attack / max(1, target.defense))
        # roll-based multipliers:
        if category == "weak":
            multiplier = 0.6
        elif category == "normal":
            multiplier = 1.0
        elif category == "strong":
            multiplier = 1.3
        elif category == "crit":
            multiplier = 1.8
        else:
            multiplier = 1.0
        # Slight random element too (small)
        variance = random.uniform(0.9, 1.1)
        damage = int(max(1, base * multiplier * variance))
        target.hp = max(0, target.hp - damage)
        context.log(f"{user.name} used {context.current_move_name} — dealt {damage} damage! ({category.upper()})")
        return damage

    @staticmethod
    def buff_attack(user: Character, target: Character, bp: int, context: "BattleSystem", roll: RollResult):
        """Apply a temporary attack buff to user."""
        # bp unused here; create buff for 3 turns
        user.add_status("javaBien", 3)
        context.log(f"{user.name} used {context.current_move_name} — attack roll boosted for 3 turns!")

    @staticmethod
    def inflict_status(user: Character, target: Character, bp: int, context: "BattleSystem", roll: RollResult):
        """Low damage plus chance to inflict javaPause (stun)."""
        MoveEffects.basic_damage(user, target, bp, context, roll)
        # simple chance: on strong/crit it's guaranteed, normal 25%, weak 5%
        _, category = roll
        chance = {"weak": 0.05, "normal": 0.25, "strong": 1.0, "crit": 1.0}[category]
        if random.random() < chance:
            target.add_status("javaPause", 2)
            context.log(f"{target.name} is stunned by {context.current_move_name}!")

    @staticmethod
    def charge_move(user: Character, target: Character, bp: int, context: "BattleSystem", roll: RollResult):
        """Consumes all charge and deals scaled damage."""
        # damage scales with current charge (>=1), consumes it
        charge_factor = max(1.0, user.charge)
        damage = MoveEffects.basic_damage(user, target, int(bp * charge_factor), context, roll)
        context.log(f"{user.name} expended charge ({round(user.charge,1)}) for extra damage!")
        user.charge = 0.0
        return damage

    @staticmethod
    def jeudiSoir_move(user: Character, target: Character, bp: int, context: "BattleSystem", roll: RollResult):
        """Powerful buff and roll boost for X turns then applies retour2Cuite at expiry."""
        # Give jeudiSoir for 2 turns (strong buff), also do damage
        MoveEffects.basic_damage(user, target, bp, context, roll)
        user.add_status("jeudiSoir", 2)
        context.log(f"{user.name} used {context.current_move_name} — massive empowerment for 2 turns!")

# map function names to actual callables for quick lookup
MOVE_FUNCTIONS = {
    "basic_damage": MoveEffects.basic_damage,
    "buff_attack": MoveEffects.buff_attack,
    "inflict_status": MoveEffects.inflict_status,
    "charge_move": MoveEffects.charge_move,
    "jeudiSoir_move": MoveEffects.jeudiSoir_move,
}

# ----------------------------
# UI Helper
# ----------------------------
class UI:
    @staticmethod
    def draw_text(surface, text, pos, font=FONT, color=WHITE):
        surf = font.render(text, True, color)
        surface.blit(surf, pos)

    @staticmethod
    def draw_centered_text(surface, text, rect, font=FONT, color=WHITE):
        surf = font.render(text, True, color)
        r = surf.get_rect(center=rect.center)
        surface.blit(surf, r.topleft)

    @staticmethod
    def draw_bar(surface, rect, value, max_value, border_color=WHITE, fill_color=GREEN):
        pygame.draw.rect(surface, border_color, rect, 1)
        inner_w = max(0, int((rect.width - 4) * (value / max_value)))
        inner_r = pygame.Rect(rect.left + 2, rect.top + 2, inner_w, rect.height - 4)
        pygame.draw.rect(surface, fill_color, inner_r)

    @staticmethod
    def draw_character_placeholder(surface, rect, char: Character, flipped=False, state="idle"):
        # simple rectangle, name and HP bar above
        pygame.draw.rect(surface, DARK, rect)
        pygame.draw.rect(surface, char.color, rect.inflate(-10, -10))
        UI.draw_text(surface, char.name, (rect.left + 6, rect.top + 6))
        # draw a simple "frame" to indicate attack animation
        if state == "attack":
            pygame.draw.rect(surface, YELLOW, rect, 4)

# ----------------------------
# Battle System
# ----------------------------
class BattleSystem:
    """
    Handles the battle loop, turn order, rolls, status application, charge, and logs.
    """

    def __init__(self, player1: Character, player2: Character):
        self.players = [player1, player2]  # index 0 is P1, 1 is P2
        # decide who goes first with a coin flip
        self.first_index = random.choice([0, 1])
        self.second_index = 1 - self.first_index
        self.current_index = self.first_index
        # second player gets a small advantage: small defense boost and initial charge
        self.players[self.second_index].defense += 2
        self.players[self.second_index].charge += 0.5
        self.log_messages: List[str] = []
        self.current_move_name = ""
        # store last roll to display
        self.last_roll: Optional[RollResult] = None
        self.roll_display_timer = 0  # frames to display roll
        # declare battle end state
        self.winner: Optional[Character] = None

    def log(self, message: str):
        print("[LOG]", message)
        self.log_messages.insert(0, message)
        if len(self.log_messages) > 6:
            self.log_messages.pop()

    def do_attack_roll(self, attacker: Character, defender: Character) -> RollResult:
        """Roll D20 and apply roll modifiers from statuses."""
        base_roll = random.randint(1, 20)
        mod = attacker.get_roll_modifier()
        roll_total = max(1, base_roll + mod)
        # Determine category
        if roll_total <= 5:
            category = "weak"
        elif 6 <= roll_total <= 15:
            category = "normal"
        elif 16 <= roll_total <= 19:
            category = "strong"
        else:  # 20 or more after modifiers
            category = "crit"
        self.last_roll = (roll_total, category)
        self.roll_display_timer = FPS * 2  # show for 2 seconds
        self.log(f"Roll: {roll_total} ({category})")
        return self.last_roll

    def apply_move(self, attacker_idx: int, move_key: str):
        """Main entry to execute a move chosen by attacker."""
        attacker = self.players[attacker_idx]
        defender = self.players[1 - attacker_idx]
        move = MOVES[move_key]
        self.current_move_name = move_key
        roll = self.do_attack_roll(attacker, defender)

        # Handle status preventing action
        if "javaPause" in attacker.statuses:
            self.log(f"{attacker.name} is stunned and can't move!")
            # still tick statuses and charge, but no move executed
            return

        # Charge gain on choosing a move (before or after? we do after)
        func_name = move["function"]
        func = MOVE_FUNCTIONS.get(func_name)
        if func is None:
            self.log(f"Move {move_key} has no function assigned.")
            return

        # If charge move but charge not full, block use
        if func_name == "charge_move" and attacker.charge < 1.0:
            self.log(f"{attacker.name} tried to use {move_key} but charge not full!")
            return

        # Execute move
        result = func(attacker, defender, move["bp"], self, roll)

        # After move, handle charge gain for both players for end of turn
        # Attacker gains standard charge per attack (modified by attacker's charge_bonus)
        attacker.charge = min(3.0, attacker.charge + 0.5 * attacker.charge_bonus)
        # Defender also passively gains small charge
        defender.charge = min(3.0, defender.charge + 0.25 * defender.charge_bonus)

        # Tick statuses durations (end of turn for both)
        attacker.tick_statuses()
        defender.tick_statuses()

        # Check for death
        if not defender.is_alive():
            self.winner = attacker
            self.log(f"{defender.name} fainted! {attacker.name} wins!")

    def next_turn(self):
        """Advance turn to next alive player. Check for end of battle."""
        if self.winner:
            return
        # if current player is stunned with javaPause, we still should allow next to move after tick
        # Toggle current_index
        self.current_index = 1 - self.current_index
        # skip if current is dead
        if not self.players[self.current_index].is_alive():
            # declare winner as other
            self.winner = self.players[1 - self.current_index]
            self.log(f"{self.winner.name} wins by default!")
            return

    def update(self):
        """Call from main loop to update timers."""
        if self.roll_display_timer > 0:
            self.roll_display_timer -= 1

# ----------------------------
# Menus and Game State
# ----------------------------
class Menu:
    """Simple menu manager with a selection cursor."""

    def __init__(self, title: str, options: List[str]):
        self.title = title
        self.options = options
        self.index = 0

    def move(self, delta):
        self.index = (self.index + delta) % len(self.options)

    def select(self):
        return self.options[self.index]

# ----------------------------
# Main Game class (state machine)
# ----------------------------
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Turn-Fighter POC")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game-wide parameters (not persisted)
        self.volume = 0.5
        self.fullscreen = False
        self.muted = True

        # State: 'title', 'params', 'credits', 'char_select', 'battle', 'game_over'
        self.state = "title"

        # Title menu
        self.title_menu = Menu("Main Menu", ["Start Game", "Parameters", "Credits", "Quit"])
        # Parameters menu
        self.params_menu = Menu("Parameters", ["Volume", "Fullscreen", "Mute", "Back"])
        self.params_cursor_values = {"Volume": self.volume, "Fullscreen": self.fullscreen, "Mute": self.muted}

        # Character selection variables
        self.available_chars = list(CHARACTERS.keys())
        self.p1_choice = 0
        self.p2_choice = 1 if len(self.available_chars) > 1 else 0
        self.char_select_stage = 0  # 0 = P1 pick, 1 = P2 pick

        # Battle related:
        self.battle: Optional[BattleSystem] = None
        # For move selection UI
        self.move_cursor = 0

        # load demo characters (instances)
        self.char_instances: Dict[str, Character] = {}
        for key, cfg in CHARACTERS.items():
            c = Character(
                config_key=key,
                name=cfg["name"],
                max_hp=cfg["stats"]["hp"],
                hp=cfg["stats"]["hp"],
                attack=cfg["stats"]["attack"],
                defense=cfg["stats"]["defense"],
                charge_bonus=cfg["stats"]["charge_bonus"],
                moveset=cfg["moveset"],
                charge_move=cfg["charge_move"],
                color=(random.randint(60, 230), random.randint(60, 230), random.randint(60, 230)),
            )
            self.char_instances[key] = c

    # ----------------------------
    # State transitions
    # ----------------------------
    def start_character_selection(self):
        self.state = "char_select"
        self.p1_choice = 0
        self.p2_choice = 1 if len(self.available_chars) > 1 else 0
        self.char_select_stage = 0

    def start_battle(self):
        # instantiate fresh characters from the configs so each battle is clean
        p1_key = self.available_chars[self.p1_choice]
        p2_key = self.available_chars[self.p2_choice]
        cfg1 = CHARACTERS[p1_key]
        cfg2 = CHARACTERS[p2_key]
        p1 = Character(
            config_key=p1_key,
            name=cfg1["name"],
            max_hp=cfg1["stats"]["hp"],
            hp=cfg1["stats"]["hp"],
            attack=cfg1["stats"]["attack"],
            defense=cfg1["stats"]["defense"],
            charge_bonus=cfg1["stats"]["charge_bonus"],
            moveset=cfg1["moveset"],
            charge_move=cfg1["charge_move"],
            color=(80, 140, 220),
        )
        p2 = Character(
            config_key=p2_key,
            name=cfg2["name"],
            max_hp=cfg2["stats"]["hp"],
            hp=cfg2["stats"]["hp"],
            attack=cfg2["stats"]["attack"],
            defense=cfg2["stats"]["defense"],
            charge_bonus=cfg2["stats"]["charge_bonus"],
            moveset=cfg2["moveset"],
            charge_move=cfg2["charge_move"],
            color=(220, 120, 100),
        )
        self.battle = BattleSystem(p1, p2)
        self.move_cursor = 0
        self.state = "battle"

    # ----------------------------
    # Input handling
    # ----------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if self.state == "title":
                self.handle_title_input(event.key)
            elif self.state == "params":
                self.handle_params_input(event.key)
            elif self.state == "credits":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.state = "title"
            elif self.state == "char_select":
                self.handle_char_select_input(event.key)
            elif self.state == "battle":
                self.handle_battle_input(event.key)
            elif self.state == "game_over":
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.state = "title"

    def handle_title_input(self, key):
        if key == pygame.K_UP:
            self.title_menu.move(-1)
        elif key == pygame.K_DOWN:
            self.title_menu.move(1)
        elif key == pygame.K_RETURN:
            sel = self.title_menu.select()
            if sel == "Start Game":
                self.start_character_selection()
            elif sel == "Parameters":
                self.state = "params"
            elif sel == "Credits":
                self.state = "credits"
            elif sel == "Quit":
                self.running = False

    def handle_params_input(self, key):
        if key == pygame.K_UP:
            self.params_menu.move(-1)
        elif key == pygame.K_DOWN:
            self.params_menu.move(1)
        elif key == pygame.K_RETURN:
            sel = self.params_menu.select()
            if sel == "Back":
                self.state = "title"
            elif sel == "Mute":
                self.muted = not self.muted
                self.params_cursor_values["Mute"] = self.muted
            elif sel == "Fullscreen":
                self.fullscreen = not self.fullscreen
                self.params_cursor_values["Fullscreen"] = self.fullscreen
                if self.fullscreen:
                    self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode(SCREEN_SIZE)
            elif sel == "Volume":
                # cycle 0.0 -> 0.5 -> 1.0 -> back
                v = self.params_cursor_values["Volume"]
                choices = [0.0, 0.5, 1.0]
                idx = choices.index(v) if v in choices else 0
                idx = (idx + 1) % len(choices)
                self.volume = choices[idx]
                self.params_cursor_values["Volume"] = self.volume
        elif key == pygame.K_ESCAPE:
            self.state = "title"

    def handle_char_select_input(self, key):
        if key == pygame.K_LEFT:
            if self.char_select_stage == 0:
                self.p1_choice = (self.p1_choice - 1) % len(self.available_chars)
            else:
                self.p2_choice = (self.p2_choice - 1) % len(self.available_chars)
        elif key == pygame.K_RIGHT:
            if self.char_select_stage == 0:
                self.p1_choice = (self.p1_choice + 1) % len(self.available_chars)
            else:
                self.p2_choice = (self.p2_choice + 1) % len(self.available_chars)
        elif key == pygame.K_RETURN:
            # confirm current player's choice and advance stage
            if self.char_select_stage == 0:
                # ensure not choosing same char for both if only 2+ choices
                self.char_select_stage = 1
            else:
                # done selecting both
                # if same character chosen for both, allow it but it's fine
                self.start_battle()
        elif key == pygame.K_ESCAPE:
            self.state = "title"

    def handle_battle_input(self, key):
        if not self.battle:
            return
        bs = self.battle
        if bs.winner:
            self.state = "game_over"
            return
        # Control available to current player only
        current = bs.current_index
        current_char = bs.players[current]
        # Navigation through move list
        moves = current_char.moveset + [current_char.charge_move if current_char.charge >= 1.0 else "(Charge)"]
        if key == pygame.K_LEFT:
            self.move_cursor = (self.move_cursor - 1) % len(moves)
        elif key == pygame.K_RIGHT:
            self.move_cursor = (self.move_cursor + 1) % len(moves)
        elif key == pygame.K_RETURN:
            selection = moves[self.move_cursor]
            if selection == "(Charge)":
                bs.log("Charge move not ready!")
                return
            # Execute move
            bs.apply_move(current, selection)
            # move animation / small pause could be handled here (simplified)
            # After performing action, advance turn
            bs.next_turn()
        elif key == pygame.K_ESCAPE:
            # quick forfeit
            bs.winner = bs.players[1 - bs.current_index]
            bs.log(f"{bs.winner.name} wins by forfeit!")
            self.state = "game_over"

    # ----------------------------
    # Rendering for different states
    # ----------------------------
    def render(self):
        self.screen.fill(BLACK)
        if self.state == "title":
            self.render_title()
        elif self.state == "params":
            self.render_params()
        elif self.state == "credits":
            self.render_credits()
        elif self.state == "char_select":
            self.render_char_select()
        elif self.state == "battle":
            self.render_battle()
        elif self.state == "game_over":
            self.render_game_over()

    def render_title(self):
        UI.draw_centered_text(self.screen, "TURN FIGHTER POC", pygame.Rect(0, 40, *SCREEN_SIZE), BIGFONT, WHITE)
        # list menu
        menu_x, menu_y = 360, 180
        for i, opt in enumerate(self.title_menu.options):
            color = YELLOW if i == self.title_menu.index else WHITE
            UI.draw_text(self.screen, opt, (menu_x, menu_y + i * 40), FONT, color)
        UI.draw_text(self.screen, "Use ↑ ↓ to move, Enter to select", (12, SCREEN_SIZE[1] - 28), FONT, GREY)

    def render_params(self):
        UI.draw_centered_text(self.screen, "PARAMETERS", pygame.Rect(0, 20, *SCREEN_SIZE), BIGFONT)
        base_x, base_y = 300, 140
        for i, opt in enumerate(self.params_menu.options):
            display = opt
            if opt == "Volume":
                display = f"Volume: {self.params_cursor_values['Volume']}"
            elif opt == "Fullscreen":
                display = f"Fullscreen: {'On' if self.params_cursor_values['Fullscreen'] else 'Off'}"
            elif opt == "Mute":
                display = f"Mute: {'On' if self.params_cursor_values['Mute'] else 'Off'}"
            color = YELLOW if i == self.params_menu.index else WHITE
            UI.draw_text(self.screen, display, (base_x, base_y + i * 40), FONT, color)
        UI.draw_text(self.screen, "ESC to return", (12, SCREEN_SIZE[1] - 28), FONT, GREY)

    def render_credits(self):
        UI.draw_centered_text(self.screen, "CREDITS", pygame.Rect(0, 20, *SCREEN_SIZE), BIGFONT)
        credits = [
            "POC Turn-Based Fighting Game",
            "Prototype by ChatGPT (POC)",
            "",
            "Controls:",
            " - Menus: ↑ ↓ Enter Esc",
            " - Battle: ← → to choose move, Enter to confirm",
            "",
            "Press Esc or Enter to return",
        ]
        for i, line in enumerate(credits):
            UI.draw_text(self.screen, line, (160, 120 + i * 28))

    def render_char_select(self):
        UI.draw_centered_text(self.screen, "Character Selection", pygame.Rect(0, 20, *SCREEN_SIZE), BIGFONT)
        # Show available characters as boxes
        box_w = 200
        spacing = 40
        start_x = 80
        y = 140
        for i, key in enumerate(self.available_chars):
            rect = pygame.Rect(start_x + i * (box_w + spacing), y, box_w, 260)
            pygame.draw.rect(self.screen, GREY if i not in (self.p1_choice, self.p2_choice) else BLUE, rect, 2)
            UI.draw_text(self.screen, CHARACTERS[key]["name"], (rect.left + 8, rect.top + 8))
            # draw stats
            cfg = CHARACTERS[key]
            s = cfg["stats"]
            UI.draw_text(self.screen, f"HP: {s['hp']} ATK: {s['attack']} DEF: {s['defense']}", (rect.left + 8, rect.top + 40))
            UI.draw_text(self.screen, f"Moves: {', '.join(cfg['moveset'])}", (rect.left + 8, rect.top + 80))
            UI.draw_text(self.screen, f"Charge: {cfg['stats']['charge_bonus']}", (rect.left + 8, rect.top + 110))
            # highlight current chooser
            if (self.char_select_stage == 0 and i == self.p1_choice) or (self.char_select_stage == 1 and i == self.p2_choice):
                pygame.draw.rect(self.screen, YELLOW, rect, 4)
        # instructions and stage
        who = "Player 1" if self.char_select_stage == 0 else "Player 2"
        UI.draw_text(self.screen, f"{who} choose your fighter. ← → to pick, Enter to confirm. ESC to cancel.", (12, SCREEN_SIZE[1] - 28))

    def render_battle(self):
        if not self.battle:
            return
        bs = self.battle
        # top area: log and last roll
        UI.draw_text(self.screen, f"Turn: {bs.players[bs.current_index].name}", (420, 10), FONT, YELLOW)
        # Draw last roll box
        roll_box = pygame.Rect(380, 40, 200, 40)
        pygame.draw.rect(self.screen, GREY, roll_box, 1)
        if bs.last_roll:
            val, cat = bs.last_roll
            UI.draw_text(self.screen, f"Last Roll: {val} ({cat})", (roll_box.left + 8, roll_box.top + 8))
        # draw two characters (P1 left, P2 right)
        left_rect = pygame.Rect(80, 110, 260, 260)
        right_rect = pygame.Rect(620, 110, 260, 260)
        UI.draw_character_placeholder(self.screen, left_rect, bs.players[0], state="idle")
        UI.draw_character_placeholder(self.screen, right_rect, bs.players[1], state="idle")
        # Draw HP and charge bars under each
        for i, char in enumerate(bs.players):
            hp_rect = pygame.Rect(80 + i * 540, 390, 260, 20)
            UI.draw_text(self.screen, f"HP: {char.hp}/{char.max_hp}", (hp_rect.left, hp_rect.top - 20))
            UI.draw_bar(self.screen, hp_rect, char.hp, char.max_hp, WHITE, GREEN)
            charge_rect = pygame.Rect(hp_rect.left, hp_rect.top + 28, 260, 14)
            UI.draw_text(self.screen, f"Charge: {round(char.charge,1)}", (charge_rect.left, charge_rect.top - 18))
            UI.draw_bar(self.screen, charge_rect, char.charge, 3.0, WHITE, BLUE)

            # statuses
            st_y = charge_rect.top + 30
            for j, s in enumerate(char.statuses.values()):
                UI.draw_text(self.screen, f"{s.name} ({'∞' if s.turns_left is None else s.turns_left})", (hp_rect.left, st_y + j * 18), font=FONT, color=ORANGE)

        # Moves UI for current player
        current = bs.current_index
        cur_char = bs.players[current]
        moves = cur_char.moveset + [cur_char.charge_move if cur_char.charge >= 1.0 else "(Charge)"]
        moves_rect = pygame.Rect(120, 480, 720, 120)
        pygame.draw.rect(self.screen, DARK, moves_rect)
        UI.draw_text(self.screen, f"{cur_char.name}'s Moves (use ← → to pick, Enter to use)", (moves_rect.left + 8, moves_rect.top + 6))
        # draw move buttons
        for i, m in enumerate(moves):
            mr = pygame.Rect(moves_rect.left + 12 + i * 180, moves_rect.top + 36, 160, 60)
            pygame.draw.rect(self.screen, GREY, mr, 2)
            color = YELLOW if i == self.move_cursor else WHITE
            UI.draw_centered_text(self.screen, m, mr, FONT, color)
            # show description if selected
            if i == self.move_cursor and m in MOVES:
                desc = MOVES[m]["desc"]
                UI.draw_text(self.screen, desc, (moves_rect.left + 12, moves_rect.top + 100), FONT, GREY)

        # Log messages
        for i, msg in enumerate(bs.log_messages):
            UI.draw_text(self.screen, msg, (20, 20 + i * 20), FONT, GREY)

        # If roll display active, show a banner
        if bs.roll_display_timer > 0 and bs.last_roll:
            val, cat = bs.last_roll
            UI.draw_centered_text(self.screen, f"ROLL -> {val} ({cat})", pygame.Rect(0, 100, *SCREEN_SIZE), BIGFONT, YELLOW)

        # If winner declared, overlay a message
        if bs.winner:
            UI.draw_centered_text(self.screen, f"{bs.winner.name} WINS!", pygame.Rect(0, 0, *SCREEN_SIZE), BIGFONT, GREEN)

    def render_game_over(self):
        UI.draw_centered_text(self.screen, "GAME OVER", pygame.Rect(0, 40, *SCREEN_SIZE), BIGFONT)
        if self.battle and self.battle.winner:
            UI.draw_centered_text(self.screen, f"Winner: {self.battle.winner.name}", pygame.Rect(0, 120, *SCREEN_SIZE), FONT)
        UI.draw_text(self.screen, "Press Enter to return to title", (12, SCREEN_SIZE[1] - 28))

    # ----------------------------
    # Main loop
    # ----------------------------
    def run(self):
        while self.running:
            for ev in pygame.event.get():
                self.handle_event(ev)

            # Update
            if self.state == "battle" and self.battle:
                self.battle.update()
                # check end conditions
                if self.battle.winner:
                    self.state = "game_over"

            self.render()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

# ----------------------------
# Entry point
# ----------------------------
def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
