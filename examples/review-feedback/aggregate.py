def aggregate_transactions(rows):
    """Summarize transaction adjustments per customer."""
    totals = {}
    for customer, amount in rows:
        totals[customer] = totals.get(customer, 0) + amount
    return [(customer, total) for customer, total in totals.items() if total]
