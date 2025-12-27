import random
from typing import Any, Callable, Union
from itertools import product

# -------------------------
# DSL core
# -------------------------
def parse_list_content(s: str) -> list:
    """Split list string content into top-level items, respecting nested brackets."""
    items = []
    depth = 0
    current = ""
    for c in s:
        if c in "[({":
            depth += 1
        elif c in "])}":
            depth -= 1
        if c == "," and depth == 0:
            items.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        items.append(current.strip())
    return items

def _choose(choices):
    """Helper to pick a random choice, evaluating callables."""
    item = random.choice(choices)
    return item() if callable(item) else item

def _choose_weighted(values, weights):
    picked = random.choices(values, weights=weights, k=1)[0]
    return picked() if callable(picked) else picked

# -------------------------
# DSL parser
# -------------------------
def make_dsl(obj: Any) -> Union[Any, Callable[[], Any]]:
    """
    Convert a DSL string, number, or nested structure into:
      - a concrete value if fully validated with v:
      - a callable producing the value at runtime otherwise
    """
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, str):
        return parse_dsl(obj)
    if isinstance(obj, list):
        choices = [make_dsl(x) for x in obj]
        fn = lambda: _choose(choices)
        # attach domain
        fn._domain = _compute_list_domain(choices)
        return fn
    raise TypeError(f"Invalid DSL type: {type(obj)}")

# -------------------------
# DSL parser
# -------------------------
BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}

def parse_dsl(s: str) -> Union[Any, Callable[[], Any]]:
    s = s.strip()

    # -------- validated "v:" --------
    if s.startswith("v:"):
        val = s[2:]
        resolved = parse_dsl(val)
        return resolved() if callable(resolved) else resolved

    # -------- range r[...] --------
    if s.startswith(("r[", "r(", "r{")):
        open_br = s[1]
        close_br = BRACKET_PAIRS[open_br]
        if not s.endswith(close_br):
            raise ValueError(f"Range must end with '{close_br}': {s}")
        inner = s[2:-1]
        parts = parse_list_content(inner)
        if len(parts) != 2:
            raise ValueError(f"Range must have exactly 2 numbers or DSL expressions: {s}")
        
        min_val = make_dsl(parts[0])
        max_val = make_dsl(parts[1])
        min_vals = resolve_numeric_domain(min_val)
        max_vals = resolve_numeric_domain(max_val)

        # check all combinations
        for a in min_vals:
            for b in max_vals:
                if a > b:
                    raise ValueError(f"Range min {a} > max {b} in {s}")

        def rng():
            a = min_val() if callable(min_val) else min_val
            b = max_val() if callable(max_val) else max_val
            return random.uniform(a, b)

        rng._domain = _compute_range_domain(min_val, max_val)
        return rng

    # -------- list l[...] --------
    if s.startswith(("l[", "l(", "l{")):
        open_br = s[1]
        close_br = BRACKET_PAIRS[open_br]
        if not s.endswith(close_br):
            raise ValueError(f"List must end with '{close_br}': {s}")
        inner = s[2:-1]
        items = parse_list_content(inner)
        if not items:
            raise ValueError(f"List cannot be empty: {s}")
        choices = [make_dsl(x) for x in items]

        sample_type = type(choices[0]() if callable(choices[0]) else choices[0])
        for c in choices[1:]:
            val = c() if callable(c) else c
            if type(val) != sample_type:
                raise TypeError(f"List items must be homogeneous: {s}")

        fn = lambda: _choose(choices)
        fn._domain = _compute_list_domain(choices)
        return fn

    # -------- weighted list wl[...] --------
    if s.startswith(("wl[", "wl(", "wl{")):
        open_br = s[2]
        close_br = BRACKET_PAIRS[open_br]
        if not s.endswith(close_br):
            raise ValueError(f"Weighted list must end with '{close_br}': {s}")
        inner = s[3:-1]
        items = parse_list_content(inner)
        if not items:
            raise ValueError(f"Weighted list cannot be empty: {s}")

        values, weights = [], []
        for item in items:
            item = item.strip()
            if not (item.startswith("(") and item.endswith(")")):
                raise ValueError(f"Weighted list item must be a 2-tuple: {item}")
            val_str, weight_str = parse_list_content(item[1:-1])
            values.append(make_dsl(val_str))
            weights.append(float(weight_str))

        sample_type = type(values[0]() if callable(values[0]) else values[0])
        for v in values[1:]:
            val = v() if callable(v) else v
            if type(val) != sample_type:
                raise TypeError(f"Weighted list items must be homogeneous: {s}")

        fn = lambda: _choose_weighted(values, weights)
        fn._domain = _compute_list_domain(values)
        return fn

    # -------- literal number --------
    try:
        return float(s)
    except Exception:
        pass

    # -------- fallback literal string --------
    return s

# -------------------------
# DSL domain helper
# -------------------------
def get_domain(obj):
    """
    Return the domain of a DSL object or literal.
    Returns:
      - iterable of possible values
      - or a single-value set for constants
    """
    if callable(obj):
        dom = getattr(obj, "_domain", None)
        if dom is None:
            raise ValueError("Callable has no domain metadata")
        return dom

    return {obj}

# -------------------------
def _compute_list_domain(choices):
    """Compute symbolic domain for a list of DSL callables or values."""
    dom = set()
    ranges = []
    for c in choices:
        if callable(c):
            d = getattr(c, "_domain", None)
            if isinstance(d, tuple) and all(isinstance(x, (int, float)) for x in d):
                # symbolic range
                ranges.append(d)
            elif isinstance(d, set):
                dom.update(d)
        else:
            dom.add(c)
    return dom.union({r for r in ranges})

def _compute_range_domain(min_val, max_val):
    # Resolve min
    if callable(min_val):
        dom = getattr(min_val, "_domain", None)
        if isinstance(dom, set):
            min_val = min(dom)
        elif isinstance(dom, tuple):
            min_val = dom[0]
        else:
            raise TypeError("Invalid domain for range min")
    # Resolve max
    if callable(max_val):
        dom = getattr(max_val, "_domain", None)
        if isinstance(dom, set):
            max_val = max(dom)
        elif isinstance(dom, tuple):
            max_val = dom[1]
        else:
            raise TypeError("Invalid domain for range max")
    return (min_val, max_val)

def resolve_numeric_domain(val):
    if callable(val):
        dom = getattr(val, "_domain", None)
        if dom is None:
            # fallback: evaluate once and wrap in list
            return [val()]
        # dom can be set of values or tuple (min,max)
        if isinstance(dom, set):
            return [x for x in dom if isinstance(x, (int, float))]
        elif isinstance(dom, tuple) and len(dom) == 2:
            return list(dom)
        else:
            raise TypeError(f"Cannot resolve domain for {val}")
    elif isinstance(val, (int, float)):
        return [val]
    else:
        raise TypeError(f"Range endpoints must be numeric or DSL returning numeric, got {val}")

# -------------------------
# Comparison helpers
# -------------------------
def check(expr: str, **vars):
    """
    Check that expr holds for all possible values of the given variables.
    Each variable can be:
      - a static value
      - a DSL callable (random value)
      - a list / weighted list / range DSL
    Example:
        check("0 <= x <= y", x=r[1,5], y=10)
    """
    # Build the domain for each variable
    domains = {}
    for name, val in vars.items():
        dom = get_domain(val)
        norm = []
        if len(dom) == 1:
            norm = list(dom)
        else:
            for d in dom:
                if isinstance(d, tuple) and len(d) == 2:
                    norm.extend(d)  # range endpoints
                else:
                    norm.append(d)
        domains[name] = norm

    # Test all combinations
    for combination in product(*domains.values()):
        local = dict(zip(domains.keys(), combination))
        try:
            if not eval(expr, {}, local):
                raise ValueError(f"Check failed for values {local}: {expr}")
        except Exception as e:
            raise ValueError(f"Check evaluation error for values {local}: {e}")

# -------------------------
# Base types
# -------------------------
class RandomNumber(float):
    """Float with DSL support."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        # Direct pass-through for callables
        if callable(v):
            return v

        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            val = parse_dsl(v)
            return val
        raise TypeError(f"RandomNumber must be int, float, or DSL string, got {type(v)}")

class RandomInt(RandomNumber):
    """Int with DSL support."""
    @classmethod
    def validate(cls, v, info=None):
        val = super().validate(v)
        if isinstance(val, float):
            return int(val)
        return val

class RandomString(str):
    """String with DSL support."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        # Direct pass-through for callables
        if callable(v):
            return v
        
        if isinstance(v, str):
            val = parse_dsl(v)
            return val
        raise TypeError(f"RandomString must be a string or DSL string, got {type(v)}")

# -------------------------
# Aliases
# -------------------------
NUM = Union[int, float]
RNUM = Union[RandomNumber, NUM, Callable[[], Any]]
RINT = Union[RandomInt, int, Callable[[], Any]]
RSTR = Union[RandomString, str, Callable[[], Any]]
RVAL = Union[RNUM, RSTR]

# -------------------------
# Self-test
# -------------------------
if __name__ == "__main__":
    test_cases = [
        "v:r[1,5]",
        "r[10,20]",
        "l[1, 2, r[3,4]]",
        "wl[(1,2),(r[5,6],1)]",
        "v:l[1,2,3,v:r[10,15]]",
        "just a string", # literal string
        "123.45",        # literal number
        "l['a','b','c']",
        "wl[('x',1),('y',2)]",
        "r[0,1]",
        "v:r[0,1]"
    ]

    print("=== DSL Test ===")
    for tc in test_cases:
        val = parse_dsl(tc)
        print(f"DSL: {tc} -> {val} (callable? {callable(val)})")
        if callable(val):
            print(f"  evaluated: {val()}")
            print(f"  domain: {get_domain(val)}")
    print("-" * 60)

    print("=== Comparison Tests ===")
    # Basic ranges
    val1 = parse_dsl("r[0,10]")
    val2 = parse_dsl("l[1,2,3]")
    val3 = parse_dsl("v:r[5,7]")

    try:
        check("0 <= x <= 10", x=val1)
        print("Check passed: 0 <= x <= 10")
    except ValueError as e:
        print("Check failed:", e)

    try:
        check("x in [1,2,3]", x=val2)
        print("Check passed: x in [1,2,3]")
    except ValueError as e:
        print("Check failed:", e)

    try:
        check("5 <= x < 10", x=val3)
        print("Check passed: 5 <= x < 10")
    except ValueError as e:
        print("Check failed:", e)

    # Expected failures
    val4 = parse_dsl("r[20,30]")
    try:
        check("x < 10", x=val4)
    except ValueError as e:
        print("Expected failure:", e)

    val5 = parse_dsl("l[10, 20, 30]")
    try:
        check("x in [5,6,7]", x=val5)
    except ValueError as e:
        print("Expected failure:", e)

    # Nested list
    val6 = parse_dsl("l[1,2,r[3,4]]")
    print(f"Nested list domain: {get_domain(val6)}")

    # Weighted list
    val7 = parse_dsl("wl[(1,2),(r[5,6],1)]")
    print(f"Weighted list domain: {get_domain(val7)}")

    # More comparison tests
    val8 = parse_dsl("r[0.5,1.5]")
    val9 = parse_dsl("r[1,1]")
    val10 = parse_dsl("l[2,3,4]")

    for v, expr in [(val8, "0 <= x <= 2"),
                    (val9, "x == 1"),
                    (val10, "x in [1,2,3,4]"),
                    (val10, "x > 1")]:
        try:
            check(expr, x=v)
            print(f"Check passed: {expr}")
        except ValueError as e:
            print(f"Check failed: {expr} -> {e}")

    print("=== All tests done ===")
