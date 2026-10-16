import unittest
from decimal import Decimal as D

from susu import (Group, parse_amount, DuplicateMemberError, GroupStateError,
                  InvalidAmountError, OverpaymentError, UnknownMemberError)


def make(*names, amount="50.00"):
    g = Group(amount)
    for n in names:
        g.add_member(n)
    return g


class SpecExample(unittest.TestCase):
    def test_full_example_from_brief(self):
        g = make("Ama", "Kofi", "Esi")
        g.record_contribution("Ama", "50")
        g.record_contribution("Kofi", "50")
        g.record_contribution("Esi", "30")
        r = g.close_week()
        self.assertFalse(r.closed)
        self.assertEqual(r.owing, {"Esi": D("20.00")})
        self.assertEqual(g.payouts, [])
        g.record_contribution("Esi", "20")
        r = g.close_week()
        self.assertTrue(r.closed)
        self.assertEqual((r.payout.member, r.payout.amount), ("Ama", D("150.00")))
        self.assertEqual(g.current_week, 2)
        self.assertEqual(g.next_recipient(), "Kofi")


class Contributions(unittest.TestCase):
    def test_partial_payments_accumulate(self):
        g = make("Ama", "Kofi")
        self.assertEqual(g.record_contribution("Ama", "10.10"), D("39.90"))
        self.assertEqual(g.record_contribution("Ama", "39.90"), D("0.00"))
        self.assertEqual(g.owed("Ama"), D("0.00"))

    def test_overpayment_rejected_including_after_partial(self):
        g = make("Ama")
        g.record_contribution("Ama", "30")
        with self.assertRaises(OverpaymentError):
            g.record_contribution("Ama", "20.01")
        self.assertEqual(g.paid("Ama"), D("30.00"))   # state unchanged

    def test_paying_when_already_full_rejected(self):
        g = make("Ama")
        g.record_contribution("Ama", "50")
        with self.assertRaises(OverpaymentError):
            g.record_contribution("Ama", "0.01")

    def test_zero_negative_and_bad_amounts_rejected(self):
        g = make("Ama")
        for bad in ("0", "0.00", "-5", "abc", "", "NaN", "Infinity", "1.005", 12.5):
            with self.assertRaises(InvalidAmountError, msg=repr(bad)):
                g.record_contribution("Ama", bad)

    def test_unknown_member_rejected(self):
        g = make("Ama")
        with self.assertRaises(UnknownMemberError):
            g.record_contribution("Nobody", "10")

    def test_only_current_week_accepted(self):
        g = make("Ama")
        with self.assertRaises(GroupStateError):
            g.record_contribution("Ama", "10", week=2)
        g.record_contribution("Ama", "10", week=1)


class Members(unittest.TestCase):
    def test_duplicate_rejected_case_insensitive(self):
        g = make("Ama")
        with self.assertRaises(DuplicateMemberError):
            g.add_member(" ama ")

    def test_cannot_add_after_first_payment(self):
        g = make("Ama", "Kofi")
        g.record_contribution("Ama", "1")
        with self.assertRaises(GroupStateError):
            g.add_member("Esi")


class ClosingWeeks(unittest.TestCase):
    def test_week_cannot_close_when_nobody_paid(self):
        g = make("Ama", "Kofi")
        r = g.close_week()
        self.assertFalse(r.closed)
        self.assertEqual(r.owing, {"Ama": D("50.00"), "Kofi": D("50.00")})
        self.assertEqual(g.current_week, 1)

    def test_cannot_close_with_no_members(self):
        with self.assertRaises(GroupStateError):
            Group("50").close_week()

    def test_full_cycle_pays_in_join_order_then_completes(self):
        g = make("Ama", "Kofi", "Esi")
        for _ in range(3):
            for m in g.members:
                g.record_contribution(m, "50")
            self.assertTrue(g.close_week().closed)
        self.assertEqual([p.member for p in g.payouts], ["Ama", "Kofi", "Esi"])
        self.assertTrue(g.is_complete)
        with self.assertRaises(GroupStateError):
            g.close_week()
        with self.assertRaises(GroupStateError):
            g.record_contribution("Ama", "1")

    def test_payments_do_not_carry_over_to_next_week(self):
        g = make("Ama", "Kofi")
        g.record_contribution("Ama", "50"); g.record_contribution("Kofi", "50")
        g.close_week()
        self.assertEqual(g.owed("Ama"), D("50.00"))


class Money(unittest.TestCase):
    def test_no_float_error(self):
        g = make("Ama", amount="0.30")
        g.record_contribution("Ama", "0.10")
        g.record_contribution("Ama", "0.20")
        self.assertEqual(g.owed("Ama"), D("0.00"))

    def test_float_input_rejected(self):
        with self.assertRaises(InvalidAmountError):
            parse_amount(0.1)

    def test_invalid_weekly_amount(self):
        for bad in ("0", "-1", "x"):
            with self.assertRaises(InvalidAmountError):
                Group(bad)


class Persistence(unittest.TestCase):
    def test_round_trip(self):
        g = make("Ama", "Kofi")
        g.record_contribution("Ama", "12.34")
        g2 = Group.from_dict(g.to_dict())
        self.assertEqual(g2.owed("Ama"), D("37.66"))
        self.assertEqual(g2.members, ["Ama", "Kofi"])


if __name__ == "__main__":
    unittest.main()
