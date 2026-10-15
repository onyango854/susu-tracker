# Susu Group Tracker

A small command-line program that manages one rotating savings group (susu) in GHS.
Python 3.8+, standard library only (no installs needed).

## Run

```bash
python -m susu                 # interactive; state saved to susu_state.json
python -m susu --file my.json  # use a different state file
python -m susu --file ""       # don't persist anything
```

Commands:

| Command | Meaning |
|---|---|
| `new 50.00` | create the group with a weekly contribution |
| `add Ama` | add a member (join order = payout order) |
| `pay Ama 30.00 [week]` | record a (partial) payment for the current week |
| `close` | close the week; pays out only if everyone paid in full |
| `report` | current week, paid in full, who owes what, payout history |
| `help`, `quit` | |

Example session (the one from the brief):

```
susu> new 50.00
susu> add Ama
susu> add Kofi
susu> add Esi
susu> pay Ama 50
susu> pay Kofi 50
susu> pay Esi 30
susu> close
Week 1 cannot close - no payout made.
  Esi owes 20.00
susu> pay Esi 20
susu> close
Week 1 closed. Ama receives GHS 150.00. Week 2 begins; Kofi is next.
```

Commands can also be piped in: `printf 'new 50\nadd Ama\nreport\n' | python -m susu --file ""`

## Tests

```bash
python -m unittest discover -v
```

## Layout

- `susu/money.py` – exact amount parsing/formatting (`Decimal`, 2 dp)
- `susu/group.py` – all business rules (no I/O)
- `susu/report.py` – report rendering
- `susu/cli.py` – command parsing, JSON persistence
- `tests/` – domain tests and CLI flow test
