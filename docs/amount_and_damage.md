## ** Damage Formula Overview**

The damage system is built in **two main steps**:

1. **Effective Amount** – calculates the base move effect including flat/stat-based damage, STAB, type multiplier, and charge bonus.
2. **Full Damage** – multiplies Effective Amount by a soft A/D factor, critical hits, and accounts for piercing.

---

## ** Parameters**

| Parameter            | Description                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `B`                  | Base value of the move: flat damage or stat-based percentage (e.g., `0.8 * attacker_attack`) |
| `S_x`                | Attacker stat to scale with if percentage-based (e.g., Attack, Magic)                        |
| `C_a`                | Attacker charge level (0 → `MAX_CHARGE`)                                                     |
| `C_d`                | Defender charge level (0 → `MAX_CHARGE`)                                                     |
| `C_max`              | Maximum charge (used for normalization)                                                      |
| `C_b`                | Charge bonus to effective amount (fraction of base, e.g., 0.5 = up to +50%)                  |
| `M`                  | Multiplicative modifier (e.g., buffs)                                                        |
| `A`                  | Additive flat bonus (e.g., small fixed bonuses)                                              |
| `S`                  | STAB multiplier (Same-Type Attack Bonus)                                                     |
| `T`                  | Type effectiveness multiplier (e.g., 0.5, 1, 1.5)                                            |
| `AD_base`            | Base A/D multiplier at equal stats (usually 1.0)                                             |
| `AD_scale`           | Maximum additional multiplier from stats (e.g., 3.0 → +3× max)                               |
| `AD_sharp`           | Sharpness of the stat advantage curve (e.g., 0.002)                                          |
| `STAT_SOFT_EXPONENT` | Softening exponent for large stat differences (diminishing returns, e.g., 0.9)               |
| `C_i`                | Influence of charge difference on A/D factor (e.g., 0.5)                                     |
| `crit_mult`          | Multiplier applied if critical hit occurs (e.g., 1.5)                                        |
| `pierce_ratio`       | Portion of defender's stat ignored (e.g., 0.5 = ignore 50% defense)                          |
| `A_s`                | Attacker stat used for A/D comparison                                                        |
| `D_s`                | Defender stat used for A/D comparison                                                        |

---

## ** Effective Amount**

[
\text{EffectiveAmount} = ((\text{BaseValue} + \text{BaseValue} \cdot C_b \cdot \frac{C_a}{C_{\max}}) \cdot M + A) \cdot S \cdot T
]

* `BaseValue = B` (flat) or `B * S_x` (stat-based)
* `C_b * C_a / C_max` → gives bonus from charge level
* `M` → multiplicative buffs (spells, potions)
* `A` → additive flat bonuses
* `S` → STAB
* `T` → type effectiveness

---

## ** Soft A/D Factor**

[
AD_{\text{factor}} = AD_{\text{base}} + AD_{\text{scale}} \cdot \tanh \Big( AD_{\text{sharp}} \cdot (1 + C_i \cdot \frac{C_a - C_d}{C_{\max}}) \cdot \operatorname{sign}(\Delta) \cdot |\Delta|^{STAT_SOFT_EXPONENT} \Big)
]

Where:

[
\Delta = A_s - D_s \cdot (1 - \text{pierce_ratio})
]

* Applies diminishing returns to extreme stat gaps
* Charge difference tilts the curve slightly, favoring the higher charge
* `pierce_ratio` reduces effective defender stat

---

## ** Full Damage Formula**

[
\text{Damage} = \text{EffectiveAmount} \cdot AD_{\text{factor}} \cdot \text{crit_mult}
]

* `crit_mult = 1.0` normally
* `crit_mult > 1` if critical hit triggers
* Works for **damage, heal, or shield**, because `EffectiveAmount` can scale off a stat or flat value

---

### ** Notes **

* Flat damage → `B` is just a number.
* Percentage damage → `B` is a ratio (0–1) and multiplies a stat.
* Charge bonus is applied **twice**:

  1. To the effective amount → gives extra base power
  2. Tilts the A/D factor → slightly favors the attacker in comparison
* Piercing ignores part of defender's stat, effective before softening.
* Softening exponent avoids huge swings in damage when attacker is massively stronger.
* STAB and type are multiplicative with the base damage, **before A/D factor**.
