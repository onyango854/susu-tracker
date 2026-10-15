"""Interactive command-line front end. State is saved to a JSON file after each command."""
import argparse
import json
import os
import shlex
import sys

from .errors import SusuError
from .group import Group
from .money import fmt
from .report import render_report

HELP = """Commands:
  new <weekly_amount>          create a group (e.g. new 50.00)
  add <name>                   add a member (only before any payment is recorded)
  pay <name> <amount> [week]   record a contribution for the current week
  close                        close the week; pays out only if everyone paid in full
  report                       show the current state and payout history
  help | quit"""


def load(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return Group.from_dict(json.load(f))
    return None


def save(group, path):
    if path and group:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(group.to_dict(), f, indent=2)
        os.replace(tmp, path)


def execute(group, line):
    """Run one command. Returns (group, output). Raises SusuError on rule violations."""
    parts = shlex.split(line)
    if not parts:
        return group, ""
    cmd, args = parts[0].lower(), parts[1:]
    if cmd == "help":
        return group, HELP
    if cmd == "new":
        if len(args) != 1:
            raise SusuError("usage: new <weekly_amount>")
        group = Group(args[0])
        return group, f"Group created: GHS {fmt(group.weekly_amount)} per member per week."
    if group is None:
        raise SusuError("no group yet - start with: new <weekly_amount>")
    if cmd == "add" and len(args) >= 1:
        return group, f"Added {group.add_member(' '.join(args))} (position {len(group.members)})."
    if cmd == "pay" and len(args) in (2, 3):
        week = None
        if len(args) == 3:
            try:
                week = int(args[2])
            except ValueError:
                raise SusuError("week must be a whole number")
        left = group.record_contribution(args[0], args[1], week)
        who = group._resolve(args[0])
        return group, f"Recorded. {who} " + ("has paid in full." if left == 0 else f"still owes {fmt(left)}.")
    if cmd == "close" and not args:
        r = group.close_week()
        if r.closed:
            msg = f"Week {r.week} closed. {r.payout.member} receives GHS {fmt(r.payout.amount)}."
            msg += (" Cycle complete." if group.is_complete
                    else f" Week {group.current_week} begins; {group.next_recipient()} is next.")
            return group, msg
        owes = "\n".join(f"  {m} owes {fmt(a)}" for m, a in r.owing.items())
        return group, f"Week {r.week} cannot close - no payout made.\n{owes}"
    if cmd == "report" and not args:
        return group, render_report(group)
    raise SusuError(f"unknown or malformed command. Type 'help'.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Susu group tracker")
    ap.add_argument("--file", default="susu_state.json", help="state file (default: susu_state.json; '' disables saving)")
    opts = ap.parse_args(argv)
    group = load(opts.file)
    interactive = sys.stdin.isatty()
    if interactive:
        print("Susu tracker. Type 'help' for commands.")
    while True:
        try:
            line = input("susu> " if interactive else "")
        except EOFError:
            break
        if line.strip().lower() in ("quit", "exit"):
            break
        try:
            group, out = execute(group, line)
            save(group, opts.file)
        except SusuError as e:
            out = f"Error: {e}"
        except ValueError as e:      # shlex quoting problems
            out = f"Error: {e}"
        if out:
            print(out)


if __name__ == "__main__":
    main()
