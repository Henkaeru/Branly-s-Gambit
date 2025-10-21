import random
from .character import Character

class MoveEffects:
    @staticmethod
    def basic_damage(user: Character, target: Character, bp: int, context, roll):
        val, cat = roll
        base = bp * (user.attack / max(1, target.defense))
        mult = {"weak": 0.6, "normal": 1.0, "strong": 1.3, "crit": 1.8}.get(cat, 1.0)
        dmg = int(max(1, base * mult * random.uniform(0.9, 1.1)))
        target.hp = max(0, target.hp - dmg)
        context.log(f"{user.name} used {context.current_move_name} — {dmg} dmg! ({cat.upper()})")

    @staticmethod
    def buff_attack(user, target, bp, context, roll):
        user.add_status("javaBien", 3)
        context.log(f"{user.name} boosted their attack for 3 turns!")

    @staticmethod
    def inflict_status(user, target, bp, context, roll):
        MoveEffects.basic_damage(user, target, bp, context, roll)
        _, cat = roll
        chance = {"weak": 0.05, "normal": 0.25, "strong": 1.0, "crit": 1.0}[cat]
        import random
        if random.random() < chance:
            target.add_status("javaPause", 2)
            context.log(f"{target.name} is stunned!")

    @staticmethod
    def charge_move(user, target, bp, context, roll):
        factor = max(1.0, user.charge)
        MoveEffects.basic_damage(user, target, int(bp * factor), context, roll)
        context.log(f"{user.name} expended charge ({round(user.charge,1)})!")
        user.charge = 0.0

    @staticmethod
    def jeudiSoir_move(user, target, bp, context, roll):
        MoveEffects.basic_damage(user, target, bp, context, roll)
        user.add_status("jeudiSoir", 2)
        context.log(f"{user.name} entered jeudiSoir mode!")

MOVE_FUNCTIONS = {
    "basic_damage": MoveEffects.basic_damage,
    "buff_attack": MoveEffects.buff_attack,
    "inflict_status": MoveEffects.inflict_status,
    "charge_move": MoveEffects.charge_move,
    "jeudiSoir_move": MoveEffects.jeudiSoir_move,
}
