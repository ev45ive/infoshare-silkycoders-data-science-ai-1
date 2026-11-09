"""Audit partner workbooks locally; calculate Nordvik-only results via supplied assortment map."""
from pathlib import Path
import json, hashlib, csv
from openpyxl import load_workbook

BASE=Path(__file__).resolve().parent/"partner"
OUT=BASE/"ai_extract.csv"
MAP=BASE/"nordvik_assortment_map.csv"
FILES={
 "partner_shipments_v3.xlsx":["PartnerLineId","PartnerBrand","PartnerSKU","Destination","WeekStart","UnitsBooked","PromisedDate","Status","PartnerNote"],
 "partner_availability_v2.xlsx":["SnapshotId","PartnerBrand","PartnerSKU","Destination","AsOfDate","AvailableUnits","ReservedUnits","MOQ","AvailabilityNote"],
}
def load_map():
 with MAP.open(encoding="utf-8",newline="") as f:
  rows=list(csv.DictReader(f))
 return {r["PartnerSKU"]:r["NordvikSKUCode"] for r in rows}
def inspect(fn,expected,mapping):
 wb=load_workbook(BASE/fn,read_only=True,data_only=True); ws=wb["Partner export"]
 headers=[c.value for c in ws[3]]
 if headers!=expected: raise ValueError(f"{fn}: schema mismatch {headers}")
 ids=set(); count=0; missing=0; units=0; scoped_count=0; scoped_units=0; exceptions=[]; exception_counts={}; examples=[]; samples_by_date={}; scoped_by_date={}; below_moq_by_date={}
 def flag(issue,key,scope=False):
  exceptions.append({"id":key,"issue":issue,"in_nordvik_scope":scope})
  exception_counts[issue]=exception_counts.get(issue,0)+1
 for row in ws.iter_rows(min_row=4,values_only=True):
  count+=1; missing+=sum(v is None for v in row); key=row[0]; sku=row[2]
  if key in ids: flag("duplicate line ID",key)
  ids.add(key); in_scope=sku in mapping
  if fn.startswith("partner_shipments"):
   units+=row[5] or 0
   if in_scope: scoped_count+=1; scoped_units+=row[5] or 0
   if row[7]=="at_risk": flag("at_risk; date needs confirmation",key,in_scope)
   if row[2] is None: flag("missing partner SKU; mapping unavailable",key)
   if row[6] is None: flag("missing promised date",key,in_scope)
   if isinstance(row[8],str) and "?" in row[8]: flag("partner note contains an open question; clarify the definition",key,in_scope)
   measure=row[5]; date_value=row[4]
  else:
   free=(row[5] or 0)-(row[6] or 0); units+=free
   week=date_value=row[4]
   week=week.date().isoformat()
   if in_scope:
    scoped_count+=1; scoped_units+=free; scoped_by_date[week]=scoped_by_date.get(week,0)+free
   below_moq_by_date.setdefault(week,0)
   if row[7] is not None and free<row[7]: flag("net availability below MOQ",key,in_scope)
   if row[7] is None: flag("missing MOQ",key,in_scope)
   if row[7] is not None and free<row[7] and in_scope: below_moq_by_date[week]+=1
   measure=free; date_value=row[4]
  if in_scope:
   record={"id":key,"brand":row[1],"partner_sku":sku,"nordvik_sku":mapping.get(sku),"destination":row[3],"date":date_value,"measure":measure,"status_or_moq":row[7],"note":row[8]}
   if fn.startswith("partner_shipments"):
    if len(examples)<12: examples.append(record)
   else:
    samples_by_date.setdefault(date_value.date().isoformat(),[])
    if len(samples_by_date[date_value.date().isoformat()])<12: samples_by_date[date_value.date().isoformat()].append(record)
 wb.close()
 latest_date=max(samples_by_date) if samples_by_date else None
 if latest_date: examples=samples_by_date[latest_date]
 nordvik_exceptions={k:sum(1 for x in exceptions if x["issue"]==k and x["in_nordvik_scope"]) for k in exception_counts}
 return {"file":fn,"sheet":"Partner export","headers":headers,"rows":count,"grain":"partner SKU-destination-week line","distinct_ids":len(ids),"missing_cells":missing,"partner_catalog_measure_sum_or_nonadditive_snapshot_sum":units,"nordvik_scope_rows_across_period":scoped_count,"nordvik_units_booked_across_period":scoped_units if fn.startswith("partner_shipments") else None,"nordvik_period_stock_sum_not_additive":scoped_units if samples_by_date else None,"nordvik_latest_snapshot_units":scoped_by_date.get(latest_date) if latest_date else None,"nordvik_latest_below_moq_lines":below_moq_by_date.get(latest_date) if latest_date else None,"latest_sample_date":latest_date,"exception_count":len(exceptions),"exception_counts":exception_counts,"nordvik_exception_counts":nordvik_exceptions,"exception_examples":exceptions[:24],"nordvik_sample":examples}
def main():
 mapping=load_map()
 if not mapping: raise ValueError("assortment map contains no Nordvik SKU mappings")
 inventory=[inspect(f,h,mapping) for f,h in FILES.items()]
 # Compact, representative handoff includes in-scope examples only, not whole workbooks.
 with OUT.open("w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["source","partner_line_id","partner_brand","partner_sku","nordvik_sku","destination","date","measure","status_or_moq","partner_note"])
  for result in inventory:
   for row in result["nordvik_sample"]:
    w.writerow([result["file"],row["id"],row["brand"],row["partner_sku"],row["nordvik_sku"],row["destination"],row["date"],row["measure"],row["status_or_moq"],row["note"]])
 report={"synthetic":True,"assortment_map_rows":len(mapping),"inventory":inventory,"ai_extract":OUT.name,"ai_extract_rows":sum(len(r["nordvik_sample"]) for r in inventory),"whole_workbooks_sent_to_ai":False,"sha256":{f:hashlib.sha256((BASE/f).read_bytes()).hexdigest() for f in [*FILES,MAP.name]}}
 (BASE/"starter-report.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
 print(json.dumps(report,indent=2,default=str))
if __name__=="__main__": main()
