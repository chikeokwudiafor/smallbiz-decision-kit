"""Generates the Hilltop Coffee Roasters sample file used by the Small Business Decision Kit.

Run from the project folder:  python3 tools/generate_sample.py
"""
# The shop and every customer in it are made up. The random seed is fixed, so running this
# script always produces exactly the same file.
#
# Problems are planted on purpose, the way real exports go wrong:
#   6 rows exported twice, 1 unreadable date (13/45/2026), 3 refunds as negative amounts,
#   4 orders with no customer ID, and a final month that stops on the 17th.
import csv, json, random, datetime as dt, os

random.seed(42)
START = dt.date(2025, 8, 1)
END = dt.date(2026, 9, 17)          # deliberate partial final month
N_CUSTOMERS = 800

CHANNELS = {
    #                 share of  chance they  (unused)  typical gap  typical
    #                 customers come back              in days     order ($)
    "Walk-in":        (0.28,     0.55,        0,        16,          17.0),
    "Instagram":      (0.24,     0.28,        2,        34,          21.0),
    "Google Ads":     (0.18,     0.22,        2,        40,          24.0),
    "Referral":       (0.14,     0.78,        8,        14,          27.0),
    "Farmers Market": (0.16,     0.50,        4,        24,          19.0),
}
names = list(CHANNELS)
weights = [CHANNELS[c][0] for c in names]

span = (END - START).days
# arrival weights: slow growth over the year, a holiday bump, no brand-new customers in the last week
day_w = []
for d in range(span + 1):
    date = START + dt.timedelta(days=d)
    w = 1.0 + 1.1 * d / span
    if (date.month == 11 and date.day >= 20) or date.month == 12:
        w *= 1.6
    if d > span - 7:
        w = 0
    day_w.append(w)

def amount_for(base, date):
    a = base * random.uniform(0.65, 1.45)
    if date.month == 12:
        a *= 1.35                      # gift season
    if random.random() < 0.012:
        a *= 4                         # the occasional gift box order
    return round(a, 2)

orders = []   # dicts: date, customer, channel, amount
for i in range(1, N_CUSTOMERS + 1):
    cid = f"C{i:04d}"
    ch = random.choices(names, weights)[0]
    _, rep, extra, gap, amt = CHANNELS[ch]
    first = START + dt.timedelta(days=random.choices(range(span + 1), day_w)[0])
    dates = [first]
    if random.random() < rep:
        my_gap = gap * random.uniform(0.6, 1.5)
        if random.random() < 0.6:
            # a regular: keeps ordering until the end, unless they drift away
            n_extra = 10_000
            stop = END
            if random.random() < 0.25:
                stop = first + dt.timedelta(days=int(random.uniform(45, 420)))
        else:
            # an occasional customer: one or two more orders, spread out
            n_extra = random.randint(1, 2)
            my_gap *= 2.5
            stop = END
        d = first
        for _ in range(n_extra):
            d = d + dt.timedelta(days=max(1, round(random.gauss(my_gap, my_gap * 0.35))))
            if d > END or d > stop:
                break
            dates.append(d)
    for d in dates:
        orders.append({"date": d, "customer": cid, "channel": ch, "amount": amount_for(amt, d)})

orders.sort(key=lambda o: (o["date"], o["customer"]))
for n, o in enumerate(orders, start=10001):
    o["order_id"] = f"HC-{n}"
    o["date_text"] = o["date"].isoformat()

truth = {"planted": {}}

# refunds (real events, negative amounts, their own ids)
refund_rows = []
cands = [o for o in orders if dt.date(2025, 10, 1) <= o["date"] <= dt.date(2026, 7, 31)]
for k, o in enumerate(random.sample(cands, 3), start=1):
    rd = o["date"] + dt.timedelta(days=random.randint(3, 10))
    refund_rows.append({"order_id": f"RF-{900 + k}", "date": rd, "date_text": rd.isoformat(),
                        "customer": o["customer"], "channel": o["channel"], "amount": -o["amount"],
                        "refund_of": o["order_id"]})
truth["planted"]["refunds"] = [{"order_id": r["order_id"], "amount": r["amount"], "refund_of": r["refund_of"]} for r in refund_rows]
orders += refund_rows
orders.sort(key=lambda o: (o["date"], o["order_id"]))

# the one unreadable date (true date in May 2026)
may = [o for o in orders if o["date"].year == 2026 and o["date"].month == 5 and o["amount"] > 0]
bad = random.choice(may)
bad["date_text"] = "13/45/2026"
truth["planted"]["unreadable_date"] = {"order_id": bad["order_id"], "true_date": bad["date"].isoformat(), "amount": bad["amount"]}

# missing customer ids
pos_orders = [o for o in orders if o["amount"] > 0 and o is not bad]
missing = random.sample(pos_orders, 4)
for o in missing:
    o["customer_missing"] = True
truth["planted"]["missing_customer"] = [{"order_id": o["order_id"], "amount": o["amount"]} for o in missing]

# exact duplicate rows (an export that ran twice for a few orders)
dup_src = random.sample([o for o in pos_orders if o not in missing], 6)
truth["planted"]["duplicates"] = [{"order_id": o["order_id"], "date": o["date_text"], "amount": o["amount"]} for o in dup_src]

def row(o):
    return [o["order_id"], o["date_text"], "" if o.get("customer_missing") else o["customer"], o["channel"], f'{o["amount"]:.2f}']

export = []
for o in orders:
    export.append(row(o))
    if o in dup_src:
        export.append(row(o))


here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "sample-data", "hilltop-coffee-orders.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "order_date", "customer_id", "channel", "amount"])
    w.writerows(export)
print(f"Wrote {len(export):,} rows to sample-data/hilltop-coffee-orders.csv")
