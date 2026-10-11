# Customer totals

`aggregate_transactions(rows)` accepts an iterable of `(customer, amount)` pairs.
Customer names are strings and amounts are integer monetary units. Each pair is
an adjustment: positive amounts are charges, negative amounts are refunds, and
zero amounts are permitted.

Return a list of `(customer, total)` pairs, one for every customer that appeared
in the input. Preserve the order in which customers first appeared. A customer's
total may be positive, negative, or zero. Empty input returns an empty list. Do
not modify the input or require it to be reusable.

Address the review in REVIEW.md, preserving this contract. You may edit
aggregate.py, add meaningful regression tests, and create DISPOSITIONS.md.
Keep TASK.md, REVIEW.md, and test_aggregate.py unchanged. Keep all changes local.

Run the authored tests with `python -m unittest discover -v`.
