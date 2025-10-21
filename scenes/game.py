import pygame, sys, random
from typing import Optional, Dict

from config import *
from ui import UI
from scenes.menu import Menu
from data.characters import CHARACTERS
from data.moves import MOVES
from models.character import Character
from systems.battle import BattleSystem


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

        # Title and parameters menus
        self.title_menu = Menu("Main Menu", ["Start Game", "Parameters", "Credits", "Quit"])
        self.params_menu = Menu("Parameters", ["Volume", "Fullscreen", "Mute", "Back"])
        self.params_cursor_values = {"Volume": self.volume, "Fullscreen": self.fullscreen, "Mute": self.muted}

        # Character selection
        self.available_chars = list(CHARACTERS.keys())
        self.p1_choice = 0
        self.p2_choice = 1 if len(self.available_chars) > 1 else 0
        self.char_select_stage = 0  # 0 = P1 pick, 1 = P2 pick

        # Battle-related
        self.battle: Optional[BattleSystem] = None
        self.move_cursor = 0

        # Demo character instances for menu preview
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
        """Instantiates new characters and initializes a battle system."""
        p1_key = self.available_chars[self.p1_choice]
        p2_key = self.available_chars[self.p2_choice]
        cfg1, cfg2 = CHARACTERS[p1_key], CHARACTERS[p2_key]

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
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
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
                flags = pygame.FULLSCREEN if self.fullscreen else 0
                self.screen = pygame.display.set_mode(SCREEN_SIZE, flags)
            elif sel == "Volume":
                v = self.params_cursor_values["Volume"]
                choices = [0.0, 0.5, 1.0]
                idx = (choices.index(v) + 1) % len(choices)
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
            if self.char_select_stage == 0:
                self.char_select_stage = 1
            else:
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

        current = bs.current_index
        cur_char = bs.players[current]
        moves = cur_char.moveset + [cur_char.charge_move if cur_char.charge >= 1.0 else "(Charge)"]

        if key == pygame.K_LEFT:
            self.move_cursor = (self.move_cursor - 1) % len(moves)
        elif key == pygame.K_RIGHT:
            self.move_cursor = (self.move_cursor + 1) % len(moves)
        elif key == pygame.K_RETURN:
            selection = moves[self.move_cursor]
            if selection == "(Charge)":
                bs.log("Charge move not ready!")
                return
            bs.apply_move(current, selection)
            bs.next_turn()
        elif key == pygame.K_ESCAPE:
            bs.winner = bs.players[1 - bs.current_index]
            bs.log(f"{bs.winner.name} wins by forfeit!")
            self.state = "game_over"

    # ----------------------------
    # Rendering for each state
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

    # --- RENDER HELPERS ---
    def render_title(self):
        UI.draw_centered_text(self.screen, "TURN FIGHTER POC", pygame.Rect(0, 40, *SCREEN_SIZE), BIGFONT, WHITE)
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
            "Modular version by ChatGPT",
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
        box_w, spacing, start_x, y = 200, 40, 80, 140
        for i, key in enumerate(self.available_chars):
            rect = pygame.Rect(start_x + i * (box_w + spacing), y, box_w, 260)
            pygame.draw.rect(self.screen, GREY if i not in (self.p1_choice, self.p2_choice) else BLUE, rect, 2)
            cfg = CHARACTERS[key]
            s = cfg["stats"]
            UI.draw_text(self.screen, cfg["name"], (rect.left + 8, rect.top + 8))
            UI.draw_text(self.screen, f"HP: {s['hp']} ATK: {s['attack']} DEF: {s['defense']}", (rect.left + 8, rect.top + 40))
            UI.draw_text(self.screen, f"Moves: {', '.join(cfg['moveset'])}", (rect.left + 8, rect.top + 80))
            UI.draw_text(self.screen, f"Charge: {cfg['stats']['charge_bonus']}", (rect.left + 8, rect.top + 110))
            if (self.char_select_stage == 0 and i == self.p1_choice) or (self.char_select_stage == 1 and i == self.p2_choice):
                pygame.draw.rect(self.screen, YELLOW, rect, 4)

        who = "Player 1" if self.char_select_stage == 0 else "Player 2"
        UI.draw_text(self.screen, f"{who} choose your fighter. ← → to pick, Enter to confirm. ESC to cancel.",
                     (12, SCREEN_SIZE[1] - 28))

    def render_battle(self):
        if not self.battle:
            return
        bs = self.battle

        # Header and last roll
        UI.draw_text(self.screen, f"Turn: {bs.players[bs.current_index].name}", (420, 10), FONT, YELLOW)
        if bs.last_roll:
            val, cat = bs.last_roll
            UI.draw_text(self.screen, f"Last Roll: {val} ({cat})", (420, 40), FONT, GREY)

        # Characters
        left_rect, right_rect = pygame.Rect(80, 110, 260, 260), pygame.Rect(620, 110, 260, 260)
        UI.draw_character_placeholder(self.screen, left_rect, bs.players[0])
        UI.draw_character_placeholder(self.screen, right_rect, bs.players[1])

        # HP/Charge bars
        for i, char in enumerate(bs.players):
            hp_rect = pygame.Rect(80 + i * 540, 390, 260, 20)
            UI.draw_text(self.screen, f"HP: {char.hp}/{char.max_hp}", (hp_rect.left, hp_rect.top - 20))
            UI.draw_bar(self.screen, hp_rect, char.hp, char.max_hp, WHITE, GREEN)

            charge_rect = pygame.Rect(hp_rect.left, hp_rect.top + 28, 260, 14)
            UI.draw_text(self.screen, f"Charge: {round(char.charge, 1)}", (charge_rect.left, charge_rect.top - 18))
            UI.draw_bar(self.screen, charge_rect, char.charge, 3.0, WHITE, BLUE)

            st_y = charge_rect.top + 30
            for j, s in enumerate(char.statuses.values()):
                UI.draw_text(self.screen, f"{s.name} ({'∞' if s.turns_left is None else s.turns_left})",
                             (hp_rect.left, st_y + j * 18), FONT, ORANGE)

        # Move UI
        current = bs.current_index
        cur_char = bs.players[current]
        moves = cur_char.moveset + [cur_char.charge_move if cur_char.charge >= 1.0 else "(Charge)"]
        moves_rect = pygame.Rect(120, 480, 720, 120)
        pygame.draw.rect(self.screen, DARK, moves_rect)
        UI.draw_text(self.screen, f"{cur_char.name}'s Moves (← →, Enter)", (moves_rect.left + 8, moves_rect.top + 6))

        for i, m in enumerate(moves):
            mr = pygame.Rect(moves_rect.left + 12 + i * 180, moves_rect.top + 36, 160, 60)
            pygame.draw.rect(self.screen, GREY, mr, 2)
            color = YELLOW if i == self.move_cursor else WHITE
            UI.draw_centered_text(self.screen, m, mr, FONT, color)
            if i == self.move_cursor and m in MOVES:
                desc = MOVES[m]["desc"]
                UI.draw_text(self.screen, desc, (moves_rect.left + 12, moves_rect.top + 100), FONT, GREY)

        # Battle logs
        for i, msg in enumerate(bs.log_messages):
            UI.draw_text(self.screen, msg, (20, 20 + i * 20), FONT, GREY)

        # Winner overlay
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

            if self.state == "battle" and self.battle:
                if self.battle.winner:
                    self.state = "game_over"

            self.render()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
