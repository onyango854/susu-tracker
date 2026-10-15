from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from .errors import (DuplicateMemberError, GroupStateError, InvalidAmountError,
                     OverpaymentError, UnknownMemberError)
from .money import parse_amount


@dataclass(frozen=True)
class Payout:
    week: int
    member: str
    amount: Decimal


@dataclass(frozen=True)
class CloseResult:
    closed: bool
    week: int                              # the week that was attempted
    payout: Optional[Payout] = None        # set when closed
    owing: Dict[str, Decimal] = field(default_factory=dict)  # set when not closed


class Group:
    """One rotating savings group.

    Rules (see NOTES.md): members receive the pot in join order, one per week;
    contributions are only accepted for the current week; members can only be
    added before the first contribution is recorded; the group completes after
    every member has been paid once.
    """

    def __init__(self, weekly_amount):
        self.weekly_amount: Decimal = parse_amount(weekly_amount)
        self._members: List[str] = []
        self.current_week: int = 1
        self._paid: Dict[str, Decimal] = {}     # paid so far in the current week
        self._payouts: List[Payout] = []
        self._started = False                   # becomes True on first contribution

    # ---- queries -------------------------------------------------------
    @property
    def members(self) -> List[str]:
        return list(self._members)

    @property
    def payouts(self) -> List[Payout]:
        return list(self._payouts)

    @property
    def is_complete(self) -> bool:
        return bool(self._members) and self.current_week > len(self._members)

    @property
    def pot(self) -> Decimal:
        return self.weekly_amount * len(self._members)

    def paid(self, member: str) -> Decimal:
        return self._paid[self._resolve(member)]

    def owed(self, member: str) -> Decimal:
        return self.weekly_amount - self.paid(member)

    def next_recipient(self) -> Optional[str]:
        if self.is_complete or not self._members:
            return None
        return self._members[self.current_week - 1]

    # ---- commands ------------------------------------------------------
    def add_member(self, name: str) -> str:
        name = (name or "").strip()
        if not name:
            raise UnknownMemberError("member name cannot be empty")
        if self._started:
            raise GroupStateError("members can only be added before the first contribution is recorded")
        if name.casefold() in {m.casefold() for m in self._members}:
            raise DuplicateMemberError(f"member already exists: {name}")
        self._members.append(name)
        self._paid[name] = Decimal("0.00")
        return name

    def record_contribution(self, member: str, amount, week: Optional[int] = None) -> Decimal:
        """Record a (possibly partial) payment. Returns what the member still owes."""
        if self.is_complete:
            raise GroupStateError("the group has completed its cycle")
        name = self._resolve(member)
        if week is not None and week != self.current_week:
            raise GroupStateError(
                f"week {week} is not open for payments (current week is {self.current_week})")
        amount = parse_amount(amount)
        owed = self.weekly_amount - self._paid[name]
        if amount > owed:
            raise OverpaymentError(f"{name} only owes {owed:.2f} this week, cannot accept {amount:.2f}")
        self._paid[name] += amount
        self._started = True
        return owed - amount

    def close_week(self) -> CloseResult:
        if not self._members:
            raise GroupStateError("cannot close a week with no members")
        if self.is_complete:
            raise GroupStateError("the group has completed its cycle")
        week = self.current_week
        owing = {m: self.weekly_amount - p for m, p in self._paid.items()
                 if p < self.weekly_amount}
        if owing:
            return CloseResult(closed=False, week=week, owing=owing)
        payout = Payout(week, self._members[week - 1], self.pot)
        self._payouts.append(payout)
        self._started = True
        self.current_week += 1
        self._paid = {m: Decimal("0.00") for m in self._members}
        return CloseResult(closed=True, week=week, payout=payout)

    # ---- persistence ---------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "weekly_amount": str(self.weekly_amount),
            "members": self._members,
            "current_week": self.current_week,
            "paid": {m: str(a) for m, a in self._paid.items()},
            "payouts": [{"week": p.week, "member": p.member, "amount": str(p.amount)}
                        for p in self._payouts],
            "started": self._started,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        g = cls(data["weekly_amount"])
        g._members = list(data["members"])
        g.current_week = int(data["current_week"])
        g._paid = {m: Decimal(a) for m, a in data["paid"].items()}
        g._payouts = [Payout(p["week"], p["member"], Decimal(p["amount"])) for p in data["payouts"]]
        g._started = bool(data["started"])
        return g

    # ---- internals -----------------------------------------------------
    def _resolve(self, member: str) -> str:
        key = (member or "").strip().casefold()
        for m in self._members:
            if m.casefold() == key:
                return m
        raise UnknownMemberError(f"unknown member: {member!r}")
   

    
                
        
    
