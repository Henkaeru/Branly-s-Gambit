import random
from data.moves import MOVES
from models.move_effects import MOVE_FUNCTIONS

class BattleSystem:
    def __init__(self, p1, p2):
        self.players = [p1, p2]
        self.current_index = random.choice([0, 1])
        self.log_messages = []
        self.current_move_name = ""
        self.winner = None
        self.last_roll = None

    def log(self, msg):
        print("[LOG]", msg)
        self.log_messages.insert(0, msg)
        if len(self.log_messages) > 6:
            self.log_messages.pop()

    def do_attack_roll(self, attacker):
        roll = random.randint(1, 20) + attacker.get_roll_modifier()
        cat = "weak" if roll <= 5 else "normal" if roll <= 15 else "strong" if roll <= 19 else "crit"
        self.last_roll = (roll, cat)
        self.log(f"Roll: {roll} ({cat})")
        return self.last_roll

    def apply_move(self, idx, move_key):
        atk = self.players[idx]
        defn = self.players[1 - idx]
        move = MOVES[move_key]
        self.current_move_name = move_key
        roll = self.do_attack_roll(atk)

        if "javaPause" in atk.statuses:
            self.log(f"{atk.name} is stunned!")
            return

        func = MOVE_FUNCTIONS[move["function"]]
        func(atk, defn, move["bp"], self, roll)

        atk.charge = min(3.0, atk.charge + 0.5 * atk.charge_bonus)
        defn.charge = min(3.0, defn.charge + 0.25 * defn.charge_bonus)
        atk.tick_statuses()
        defn.tick_statuses()

        if not defn.is_alive():
            self.winner = atk
            self.log(f"{defn.name} fainted! {atk.name} wins!")

    def next_turn(self):
        if not self.winner:
            self.current_index = 1 - self.current_index
