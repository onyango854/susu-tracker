# Notes

## Assumptions / rules I chose
1. **Members can only be added before any contribution is recorded.** Payout order is
   fixed at join order, and a late joiner would have missed earlier contributions while
   still being owed a full pot (unfair). Locking the roster at the first payment keeps
   every member paying and receiving equally. Rejected with a clear error.
2. **Contributions are only accepted for the current week.** Past weeks are closed
   (they can only close when fully paid, so nothing is owed); future weeks are rejected
   because prepayment would complicate the "owes" model. The optional `week` argument
   is validated against this rule.
3. **One cycle.** The group has N members and runs N weeks; after the last member is
   paid the group is complete and further payments/closes are rejected.
4. **Closing a week with no members is an error**; closing with unpaid amounts is *not*
   an error - it returns a "not closed" result listing who owes what, and changes nothing.
5. **Names are unique case-insensitively** and trimmed ("Ama" and " ama " clash). The
   original spelling is kept for display. Lookups are also case-insensitive.
6. **Currency is GHS with 2 decimal places.** Amounts with more than 2 decimals are
   rejected (never silently rounded). Float inputs are rejected at the API level.
7. Overpayment includes paying anything once a member is already fully paid.

## Decisions
- **`Decimal`**, not float, for all money; parsed from strings in one place (`money.py`).
- The **domain (`Group`) has no I/O**; the CLI is a thin layer, so tests hit rules directly.
- `close_week` returns a `CloseResult` rather than raising for the "not everyone paid"
  case, since that is an expected outcome, not an error. Real rule violations raise
  specific `SusuError` subclasses.
- Failed operations never mutate state (validate first, then change).
- State is persisted as JSON with amounts as strings (no float round trip); written
  atomically via temp file + rename.
- Standard-library `unittest` so there is nothing to install.

## With more time
- Handle members who default: carry-over of debts, grace periods, removing a member.
- Allow joining mid-cycle with a defined catch-up rule, or multiple cycles.
- Payment ledger (timestamps, who recorded it) instead of just running totals, plus
  corrections/reversals.
- Multiple groups, and a small HTTP API on top of the same `Group` class.
- Property-based tests (e.g. total paid out == total contributed) and CI.
