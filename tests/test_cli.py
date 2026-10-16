import unittest
from susu.cli import execute
from susu import SusuError


class CliTests(unittest.TestCase):
    def test_example_flow_and_report(self):
        g = None
        for line in ["new 50.00", "add Ama", "add Kofi", "add Esi",
                     "pay Ama 50", "pay Kofi 50", "pay Esi 30"]:
            g, _ = execute(g, line)
        g, out = execute(g, "close")
        self.assertIn("Esi owes 20.00", out)
        g, _ = execute(g, "pay Esi 20")
        g, out = execute(g, "close")
        self.assertIn("Ama receives GHS 150.00", out)
        g, out = execute(g, "report")
        self.assertIn("Current week: 2", out)
        self.assertIn("Next recipient: Kofi", out)
        self.assertIn("Week 1: Ama received GHS 150.00", out)

    def test_errors_are_domain_errors(self):
        with self.assertRaises(SusuError):
            execute(None, "add Ama")


if __name__ == "__main__":
    unittest.main()
