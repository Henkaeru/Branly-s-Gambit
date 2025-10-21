MOVES = {
    "Tackle": {"name": "Tackle", "bp": 40, "function": "basic_damage", "desc": "A standard physical attack."},
    "FocusStrike": {"name": "Focus Strike", "bp": 55, "function": "basic_damage", "desc": "Strong attack with small variance."},
    "Rally": {"name": "Rally", "bp": 0, "function": "buff_attack", "desc": "Boost own attack for 3 turns."},
    "StunShot": {"name": "Stun Shot", "bp": 20, "function": "inflict_status", "desc": "Low damage + chance to stun."},
    "ChargeBurst": {"name": "Charge Burst", "bp": 120, "function": "charge_move", "desc": "Consumes charge for huge damage."},
    "JeudiBlast": {"name": "Jeudi Blast", "bp": 90, "function": "jeudiSoir_move", "desc": "Buff + roll boost, ends with hangover."},
}
