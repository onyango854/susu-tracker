from .group import Group
from .money import fmt


def render_report(g: Group) -> str:
    lines = [f"Weekly contribution: GHS {fmt(g.weekly_amount)}   Pot: GHS {fmt(g.pot)}"]
    if g.is_complete:
        lines.append("Status: cycle complete - every member has been paid.")
    else:
        lines.append(f"Current week: {g.current_week}   Next recipient: {g.next_recipient() or '-'}")
        paid_full = [m for m in g.members if g.owed(m) == 0]
        owing = [(m, g.owed(m)) for m in g.members if g.owed(m) > 0]
        lines.append("Paid in full: " + (", ".join(paid_full) if paid_full else "nobody yet"))
        if owing:
            lines.append("Owing:")
            lines += [f"  {m} owes {fmt(a)}" for m, a in owing]
        elif g.members:
            lines.append("Owing: nobody - the week can be closed")
    lines.append("Payout history:")
    if g.payouts:
        lines += [f"  Week {p.week}: {p.member} received GHS {fmt(p.amount)}" for p in g.payouts]
    else:
        lines.append("  (none yet)")
    return "\n".join(lines)
            
