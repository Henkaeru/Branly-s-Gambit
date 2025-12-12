# General constants & defaults for moves

MOVE_CATEGORIES = ["damage", "support", "special", "none"]
MOVE_TYPES = ["dev", "opti", "syst", "data", "proj", "team", "none"]

# Default values for move system

DEFAULTS = {
    "name": "unknown",
    "enabled": True,
    "type": "none",
    "category": "none",
    "charge_usage": 0.0,
    "amount": 0,
    "chance": 1.0,
    "target": "opponent",
    "calc_target": "self",
    "calc_field": "hp",
    "multiply": 1.0,
    "divide": 1.0,
    "add": 0,
    "subtract": 0,
    "duration": -1,
    "sound": None,
    "description": ""
}