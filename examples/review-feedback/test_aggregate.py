import unittest

from aggregate import aggregate_transactions


class AggregateTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(aggregate_transactions([]), [])

    def test_first_seen_order_with_refunds(self):
        rows = [("Zoe", 10), ("Ari", 7), ("Zoe", -3), ("Mina", -2)]
        original = list(rows)
        self.assertEqual(
            aggregate_transactions(rows),
            [("Zoe", 7), ("Ari", 7), ("Mina", -2)],
        )
        self.assertEqual(rows, original)

    def test_single_pass_iterable(self):
        rows = iter([("Bea", 6), ("Bea", -1), ("Ada", 3)])
        self.assertEqual(aggregate_transactions(rows), [("Bea", 5), ("Ada", 3)])


if __name__ == "__main__":
    unittest.main()
