from decimal import Decimal, InvalidOperation


def number(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("−", "-")
    if s in {"", "-", "—", "NA", "N/A"}:
        return None
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        value = Decimal(s.rstrip("%"))
        return value if value.is_finite() else None
    except InvalidOperation:
        return None


def to_crores(value, unit: str, currency="INR", kind="money"):
    if currency != "INR" or kind != "money":
        raise ValueError("Crore normalization requires INR monetary amounts")
    factors = {"rupees": Decimal("0.0000001"), "lakhs": Decimal("0.01"),
               "millions": Decimal("0.1"), "crores": Decimal(1), "billions": Decimal(100)}
    if unit not in factors:
        raise ValueError("Unknown monetary unit")
    n = number(value)
    return None if n is None else n * factors[unit]


def delta(curr, prev):
    curr, prev = number(curr), number(prev)
    if curr is None or prev is None:
        return {"percent": None, "state": "missing"}
    if prev == 0:
        return {"percent": None, "state": "zero_base"}
    if curr > 0 and prev < 0:
        state = "turnaround"
    elif curr < 0 and prev > 0:
        state = "swung_to_loss"
    elif curr == 0 and prev < 0:
        state = "loss_to_breakeven"
    elif curr < 0 and prev < 0:
        state = "loss_narrowed" if curr > prev else "loss_widened" if curr < prev else "unchanged_loss"
    else:
        return {"percent": float((curr - prev) / prev * 100), "state": "comparable"}
    return {"percent": None, "state": state}


def ratio(num, den):
    num, den = number(num), number(den)
    return None if num is None or den is None or den <= 0 else num / den
