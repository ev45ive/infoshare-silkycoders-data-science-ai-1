from pathlib import Path
import csv, sqlite3
base=Path(__file__).parent
con=sqlite3.connect(':memory:')
con.executescript((base/'source_schema.sql').read_text(encoding='utf-8'))
with (base/'sales_lines.csv').open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
con.executemany('INSERT INTO src_SalesRaw VALUES(?,?,?,?,?,?,?,?)', [(r['SaleDate'],r['StoreCode'],r['TransactionNo'],int(r['LineNumber']),int(r['Quantity']),float(r['GrossAmount']),float(r['DiscountAmount']),r['Status']) for r in rows])
con.executescript((base/'staging.sql').read_text(encoding='utf-8'))
con.executescript((base/'weekly_report.sql').read_text(encoding='utf-8'))
print('reporting_WeeklySales:', con.execute('SELECT SUM(NetSales) FROM reporting_WeeklySales').fetchone()[0])
print('transactions:', con.execute("SELECT COUNT(DISTINCT TransactionNo) FROM dbo_FactSales WHERE Status='POSTED'").fetchone()[0])
