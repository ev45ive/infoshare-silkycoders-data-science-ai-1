"""Ścieżki i limity asystenta BC-09 (bez sekretów: klucz API tylko ze zmiennej środowiskowej)."""
from pathlib import Path

ANALIZA = Path(__file__).resolve().parents[3]            # analizy/bc09-asystent-analityczny (core leży w usluga/service/core)
REPO = ANALIZA.parents[1]
DATA = REPO / "datasets" / "synthetic" / "bc09"
DOCS = DATA / "docs_procedury"
CACHE = ANALIZA / "cache"
WYNIKI = ANALIZA / "wyniki"
DB_PATH = CACHE / "nordvik_bc09.duckdb"
TASKS_PATH = CACHE / "zadania_szkice.json"
LEDGER_PATH = CACHE / "llm_zuzycie.json"

# Limity bezpieczeństwa narzędzia SQL
SQL_MAX_ROWS = 200
SQL_TIMEOUT_S = 15
ALLOWED_SCHEMAS = ("dbo", "reporting")

# Katalog kolumn, które nie liczą tego, co sugeruje nazwa (wynik audytu F2). To konfiguracja, nie logika narzędzia.
COLUMN_WARNINGS = {
    ("vw_salesdaily", "revenue"): "reporting.vw_SalesDaily.Revenue to sprzedaż BRUTTO (z VAT); wg słownika sprzedaż netto = SUM(dbo.FactSales.NetAmount).",
    ("vw_stockavailability", "availabilitypct"): "AvailabilityPct dzieli przez cały katalog SKU; wg słownika dostępność = SkuAvailable / SkuInFeed.",
    ("vw_storescorecard", "grossmargin"): "GrossMargin nie odejmuje zwrotów; wg słownika marża brutto = NetSales - CostOfGoods - ReturnsNet.",
    ("vw_salesweekly", "transactions"): "Transactions w widoku tygodniowym to DISTINCT per komórka; suma po komórkach zawyża liczbę transakcji (użyj COUNT(DISTINCT TransactionNo) z dbo.FactSales).",
}

# Limity agenta
MAX_STEPS = 8                  # maks. wywołań narzędzi na pytanie
LLM_MODEL = "gpt-4.1-mini"
EMBED_MODEL = "text-embedding-3-small"
TOTAL_TOKEN_LIMIT = 3_000_000  # łączny twardy limit (wejście + wyjście) dla BC-09, wszystkie sesje
PER_QUESTION_TOKEN_LIMIT = 60_000
