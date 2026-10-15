"""Exact money handling. All amounts are Decimal with exactly 2 places (GHS)."""
from decimal import Decimal, InvalidOperation

from .errors import InvalidAmountError

_CENT = Decimal("0.01")


def parse_amount(value, *, allow_zero=False) -> Decimal:
    """Convert str/int/Decimal to an exact 2dp Decimal.

    Floats are rejected on purpose (0.1 + 0.2 != 0.3). More than 2 decimal
    places is rejected rather than silently rounded.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidAmountError("amount must be a string, int or Decimal, not float/bool")
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise InvalidAmountError(f"not a valid amount: {value!r}")
    if not d.is_finite():
        raise InvalidAmountError(f"not a valid amount: {value!r}")
    if d != d.quantize(_CENT):
        raise InvalidAmountError("amount cannot have more than 2 decimal places")
    d = d.quantize(_CENT)
    if d < 0 or (d == 0 and not allow_zero):
        raise InvalidAmountError("amount must be greater than zero")
    return d


def fmt(amount: Decimal) -> str:
    return f"{amount:.2f}"
