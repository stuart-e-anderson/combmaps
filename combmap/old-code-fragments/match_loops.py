for d1 in darts:
    for d2 in darts:
        if d1.origin == d2.target and d1.target == d2.origin:
            d1.reversal = d2
            d2.reversal = d1

