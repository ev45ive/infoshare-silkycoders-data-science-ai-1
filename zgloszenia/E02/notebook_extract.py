from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent
WEEK_START = '2026-10-05'
WEEK_END = '2026-10-11'
with (ROOT / 'sales_lines.csv').open(encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))
posted = [r for r in rows if r['Status'] == 'POSTED' and WEEK_START <= r['SaleDate'] <= WEEK_END]
net_sales = sum(float(r['GrossAmount']) / 1.23 for r in posted)
transaction_count = len({r['TransactionNo'] for r in posted})
print(f'notebook_net_sales={net_sales:.2f}; transactions={transaction_count}')
