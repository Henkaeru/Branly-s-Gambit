import ast
import random
from typing import Any, Union

class RandomNumber(float):
    """
    A number that can be:
      - int
      - float
      - DSL string (like "r[1,5]", "i10", "wl[...]")
    Validates the string and resolves it immediately to a number.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(resolve_random_string(v))
            except Exception as e:
                raise ValueError(f"Invalid random number string: {v}") from e
        raise TypeError(f"RandomNumber must be int, float, or string, got {type(v)}")

class RandomInt(RandomNumber):
    @classmethod
    def validate(cls, v):
        val = super().validate(v)
        return int(val)

NUM = Union[int, float]
RINT = Union[int, RandomInt]
RNUM = Union[NUM, RandomNumber]



class RandomString(str):
    """
    A string that can be:
      - literal string
      - DSL string (like l[...], wl[...], nested)
    Validates the string and resolves it immediately to a string.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        # Already a string that is a literal (not DSL)
        if isinstance(v, str):
            resolved = resolve_random_string(v)
            if not isinstance(resolved, str):
                raise ValueError(f"Resolved value is not a string: {resolved}")
            return resolved
        raise TypeError(f"RandomString must be a string or DSL, got {type(v)}")
    
RSTR = Union[str, RandomString]
RVAL = Union[RNUM, RSTR]



def resolve_random_string(s: Any) -> Any:
    """
    Resolve a DSL random string or nested structure to a concrete number or string.
    
    Supports:
      - 3, 4.5   -> literal number
      - r[1,5]   -> random float between 1 and 5
      - l[1,2,"a",["c","d"],r[3,4]] -> pick recursively from nested list
      - wl[(r[1,2],1),("x",4),(2,4)] -> weighted random choice, recursive
    """

    # If already a number, return as-is
    if isinstance(s, (int, float)):
        return s

    if not isinstance(s, str):
        raise TypeError(f"Invalid type for random resolution: {type(s)}")

    s = s.strip()

    # -------- Range ----------
    if s.startswith("r"):
        inner = s[1:].strip()
        if inner[0] not in "([{" or inner[-1] not in ")]}":
            raise ValueError(f"Invalid range syntax: {s}")
        parts = [x.strip() for x in inner[1:-1].split(",")]
        if len(parts) != 2:
            raise ValueError(f"Range must have exactly 2 numbers: {s}")
        min_val, max_val = float(parts[0]), float(parts[1])
        if min_val > max_val:
            raise ValueError(f"Range min cannot be greater than max: {s}")
        return random.uniform(min_val, max_val)

    # -------- List ----------
    elif s.startswith("l"):
        inner = s[1:].strip()
        if inner[0] not in "([{" or inner[-1] not in ")]}":
            raise ValueError(f"Invalid list syntax: {s}")
        try:
            items = ast.literal_eval("[" + inner[1:-1] + "]")
        except Exception as e:
            raise ValueError(f"Invalid list content: {s}") from e
        if not isinstance(items, list):
            raise ValueError(f"List did not parse to Python list: {s}")
        choice_item = random.choice(items)
        # recursively resolve
        return resolve_random_string(choice_item) if isinstance(choice_item, (str, list)) else choice_item

    # -------- Weighted List ----------
    elif s.startswith("wl"):
        inner = s[2:].strip()
        if inner[0] not in "([{" or inner[-1] not in ")]}":
            raise ValueError(f"Invalid weighted list syntax: {s}")
        try:
            items = ast.literal_eval("[" + inner[1:-1] + "]")
        except Exception as e:
            raise ValueError(f"Invalid weighted list content: {s}") from e
        if not isinstance(items, list):
            raise ValueError(f"Weighted list did not parse to a list: {s}")
        values, weights = [], []
        for item in items:
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                raise ValueError(f"Each weighted list item must be a 2-tuple: {s}")
            val, weight = item
            # recursively resolve value if string or list
            if isinstance(val, (str, list)):
                val = resolve_random_string(val)
            values.append(val)
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise ValueError(f"Weight must be positive number: {s}")
            weights.append(float(weight))
        return random.choices(values, weights=weights, k=1)[0]

    # -------- Literal number ----------
    else:
        # try numeric literal
        try:
            return float(s)
        except Exception:
            pass
        # else just treat as string literal
        return s
