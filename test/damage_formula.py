import itertools
import math
import statistics

# ------------------------------
# Parameters
# ------------------------------
STAT_LEVELS = {"low": 50, "normal": 100, "big": 150}
CHARGE_LEVELS = {"low": 0, "normal": 500, "big": 999}
# STAB_OPTIONS = [1.0, 1.25]
# TYPE_EFFECTIVENESS = [0.0, 0.75, 1.0, 1.25]
STAB_OPTIONS = [1.0]
TYPE_EFFECTIVENESS = [1.0]
ONLY_SELECTED = True   # <- set to False to keep full sweep behavior
SHOW_STEPS = True      # <- detailed formula output

BASE_POWER = 80
MULTIPLY = 1.0
ADD = 0.0

MAX_CHARGE = 999

# ------------------------------
# A/D curve tuning
# ------------------------------
AD_BASELINE = 1.0        # neutral multiplier at equal stats
AD_SCALE = 3.0           # max additional advantage from stats
AD_SHARPNESS = 0.004     # growth speed of stat advantage
STAT_SOFT_EXPONENT = 0.9 # diminishing returns on stat stacking
CHARGE_INFLUENCE = 0.5   # how much charge tilts the curve

# ------------------------------
# Charge Bonus
# ------------------------------
CHARGE_AMOUNT_BONUS = 0.5  # % of base power at full charge


# ------------------------------
# Damage functions
# ------------------------------
def effective_amount(base_power, multiply, add,
                     stab, type_eff,
                     attacker_charge):
    charge_ratio = attacker_charge / MAX_CHARGE
    charge_bonus = base_power * CHARGE_AMOUNT_BONUS * charge_ratio

    return ((base_power + charge_bonus) * multiply + add) * stab * type_eff


def soften_stat_difference(stat_diff):
    """
    Applies diminishing returns to large stat gaps.
    """
    return math.copysign(
        abs(stat_diff) ** STAT_SOFT_EXPONENT,
        stat_diff
    )


def ad_factor_soft(attacker_stat, defender_stat,
                   attacker_charge, defender_charge):
    """
    Soft saturating A/D curve with charge influence.
    """

    # Stat difference (softened)
    raw_stat_diff = attacker_stat - defender_stat
    stat_diff = soften_stat_difference(raw_stat_diff)

    # Charge influence (tilts sharpness slightly)
    charge_delta = (attacker_charge - defender_charge) / MAX_CHARGE
    sharpness = AD_SHARPNESS * (1 + CHARGE_INFLUENCE * charge_delta)

    return AD_BASELINE + AD_SCALE * math.tanh(sharpness * stat_diff)


def effective_damage(base_power, multiply, add,
                     attacker_stat, defender_stat,
                     attacker_charge, defender_charge,
                     stab, type_eff):
    ea = effective_amount(
        base_power, multiply, add,
        stab, type_eff,
        attacker_charge
    )
    adf = ad_factor_soft(
        attacker_stat, defender_stat,
        attacker_charge, defender_charge
    )
    return ea * adf

# ------------------------------
# Selected matchups
# ------------------------------
selected_cases = [
    # ("big attacker, big charge", "low defender, low charge", "Goliath vs David"),
    # ("low attacker, low charge", "big defender, big charge", "David vs Goliath"),
    # ("big attacker, normal charge", "normal defender, normal charge", "strong vs not"),
    # ("normal attacker, normal charge", "big defender, normal charge", "not vs strong"),
    # ("big attacker, big charge", "normal defender, low charge", "charged up vs drained"),
    # ("normal attacker, low charge", "big defender, big charge", "drained vs charged up"),
    ("normal attacker, low charge", "normal defender, low charge", "even matchup"),
]

def get_val(name):
    stat_name, charge_name = name.split(", ")
    return STAT_LEVELS[stat_name.split()[0]], CHARGE_LEVELS[charge_name.split()[0]]

def explain_damage(base_power, multiply, add,
                   attacker_stat, defender_stat,
                   attacker_charge, defender_charge,
                   stab, type_eff):

    print("\n--- Damage computation ---")

    # ----- Effective amount -----
    charge_ratio = attacker_charge / MAX_CHARGE
    charge_bonus = base_power * CHARGE_AMOUNT_BONUS * charge_ratio

    print(f"Charge ratio = {attacker_charge} / {MAX_CHARGE} = {charge_ratio:.4f}")
    print(f"Charge bonus = {base_power} * {CHARGE_AMOUNT_BONUS} * {charge_ratio:.4f} = {charge_bonus:.2f}")

    ea = ((base_power + charge_bonus) * multiply + add)
    print(f"Base amount = ({base_power} + {charge_bonus:.2f}) * {multiply} + {add} = {ea:.2f}")

    ea *= stab
    print(f"After STAB ({stab}) = {ea:.2f}")

    ea *= type_eff
    print(f"After type effectiveness ({type_eff}) = {ea:.2f}")

    # ----- A/D factor -----
    raw_stat_diff = attacker_stat - defender_stat
    softened_diff = soften_stat_difference(raw_stat_diff)

    charge_delta = (attacker_charge - defender_charge) / MAX_CHARGE
    sharpness = AD_SHARPNESS * (1 + CHARGE_INFLUENCE * charge_delta)

    adf = AD_BASELINE + AD_SCALE * math.tanh(sharpness * softened_diff)

    print(f"\nStat diff = {attacker_stat} - {defender_stat} = {raw_stat_diff}")
    print(f"Softened stat diff = {softened_diff:.4f}")
    print(f"Charge delta = {charge_delta:.4f}")
    print(f"Sharpness = {sharpness:.6f}")
    print(f"A/D factor = {adf:.4f}")

    final_damage = ea * adf
    print(f"\nFinal damage = {ea:.2f} * {adf:.4f} = {final_damage:.2f}")

    return final_damage


# ------------------------------
# Run calculation
# ------------------------------
if ONLY_SELECTED:
    for att_name, def_name, label in selected_cases:
        att_stat, att_charge = get_val(att_name)
        def_stat, def_charge = get_val(def_name)

        print(f"\n==============================")
        print(f"{label.upper()}")
        print(f"Attacker: stat={att_stat}, charge={att_charge}")
        print(f"Defender: stat={def_stat}, charge={def_charge}")

        for stab in STAB_OPTIONS:
            for type_eff in TYPE_EFFECTIVENESS:
                print(f"\nSTAB={stab}, Type effectiveness={type_eff}")
                dmg = explain_damage(
                    BASE_POWER, MULTIPLY, ADD,
                    att_stat, def_stat,
                    att_charge, def_charge,
                    stab, type_eff
                )
else:
    damages = []
    highlights = []

    for att_stat in STAT_LEVELS.values():
        for att_charge in CHARGE_LEVELS.values():
            for def_stat in STAT_LEVELS.values():
                for def_charge in CHARGE_LEVELS.values():
                    for stab in STAB_OPTIONS:
                        for type_eff in TYPE_EFFECTIVENESS:
                            dmg = effective_damage(
                                BASE_POWER, MULTIPLY, ADD,
                                att_stat, def_stat,
                                att_charge, def_charge,
                                stab, type_eff
                            )
                            damages.append(dmg)

                            for att_name, def_name, label in selected_cases:
                                sel_att_stat, sel_att_charge = get_val(att_name)
                                sel_def_stat, sel_def_charge = get_val(def_name)
                                if (att_stat, att_charge, def_stat, def_charge) == (
                                    sel_att_stat, sel_att_charge,
                                    sel_def_stat, sel_def_charge
                                ):
                                    highlights.append((label, dmg, stab, type_eff))

    # ------------------------------
    # Summary
    # ------------------------------
    print("\n=== Soft A/D curve ===")
    print(f"Min damage: {min(damages):.2f}")
    print(f"Max damage: {max(damages):.2f}")
    print(f"Average damage: {statistics.mean(damages):.2f}")
    print(f"Median damage: {statistics.median(damages):.2f}")

    print("\n--- Highlights ---")
    for label, dmg, stab, type_eff in highlights:
        print(f"{label}: damage={dmg:.2f}, STAB={stab}, type_effectiveness={type_eff}")
