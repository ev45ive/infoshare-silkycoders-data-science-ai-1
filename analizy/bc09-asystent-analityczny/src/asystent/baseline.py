"""Wariant W1: pipeline regułowy bez modelu językowego (intencje regułami, szablony SQL, wyszukiwanie BM25).

Szablony wynikają ze słownika metryk (metryka x przekrój x okres), a nie z pojedynczych pytań.
"""
import re

from . import tools

# Słowniki dopasowania słów kluczowych (małe litery, prefiksy bez fleksji) do kodów sklepów, nazw kategorii i numerów miesięcy.
# Wariant W1 nie rozumie języka: rozpoznaje tylko to, co jest na tych listach.
STORES = [("arkadi", "S-WAW-01"), ("mokotów", "S-WAW-02"), ("mokotow", "S-WAW-02"), ("kraków", "S-KRK-01"), ("krakow", "S-KRK-01"),
          ("poznań", "S-POZ-01"), ("poznan", "S-POZ-01"), ("gdańsk", "S-GDA-01"), ("gdansk", "S-GDA-01"),
          ("internet", "S-ONL-01"), ("online", "S-ONL-01")]
CATS = [("kurtk", "Kurtki"), ("sukien", "Sukienki"), ("swet", "Swetry"), ("jeans", "Jeansy"), ("t-shirt", "T-shirty"),
        ("koszul", "Koszule"), ("akcesori", "Akcesoria")]
MONTHS = {"stycz": 1, "lut": 2, "marc": 3, "kwiet": 4, "maj": 5, "czerw": 6, "lip": 7, "sierp": 8, "wrze": 9, "paźdz": 10,
          "listop": 11, "grud": 12}
# Zakres z opisu firmy: brak identyfikatora klienta, pogody, cen konkurencji; asystent nie zapisuje ani nie zatwierdza.
OUT_OF_SCOPE = re.compile(r"(identyfikator\w* klient\w*|e-?mail|pogod\w*|konkurencj\w*|zaktualizuj|usuń|zatwierdź)", re.I)


def fmt(x, nd=2):
    # Polski zapis liczby: spacja jako separator tysięcy, przecinek dziesiętny (zamiana w dwóch krokach, żeby się nie zderzyły).
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def parse(q):
    # Z pytania wyciąga parametry zapytania: sklep, kategorię, tygodnie (RRRR-Wnn), dni (RRRR-MM-DD albo „10 września 2026"),
    # miesiące („sierpniu 2026") i kod modelu produktu (np. W-JKT-001). Wszystko wyrażeniami regularnymi.
    ql = q.lower()
    d = {"store": next((c for k, c in STORES if k in ql), None), "cat": next((c for k, c in CATS if k in ql), None),
         "weeks": re.findall(r"(\d{4})-W(\d{2})", q), "days": re.findall(r"\d{4}-\d{2}-\d{2}", q), "months": []}
    for m in re.finditer(r"(stycz|lut|marc|kwiet|maj|czerw|lip|sierp|wrze|paźdz|listop|grud)\w*\s+(\d{4})", ql):
        d["months"].append(f"{m.group(2)}-{MONTHS[m.group(1)]:02d}")
    for m in re.finditer(r"(\d{1,2})\s+(stycz|lut|marc|kwiet|maj|czerw|lip|sierp|wrze|paźdz|listop|grud)\w*\s+(\d{4})", ql):
        d["days"].append(f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}")
    d["style"] = (re.search(r"\b[A-Z]-[A-Z]{3}-\d{3}\b", q) or [None])[0]
    return d


def _where(p, period):
    # Warunek WHERE dla okresu: tydzień ISO po parze IsoYear + IsoWeek (nigdy samo Year), miesiąc po YearMonth, dzień po Date;
    # opcjonalnie zawężony do sklepu i kategorii. Aliasy d, st, p odpowiadają złączeniom JOIN/RJOIN poniżej.
    kind, val = period
    c = {"week": f"d.IsoYear={int(val[:4])} and d.IsoWeek={int(val[-2:])}", "month": f"d.YearMonth='{val}'", "day": f"d.Date=DATE '{val}'"}[kind]
    if p["store"]:
        c += f" and st.StoreCode='{p['store']}'"
    if p["cat"]:
        c += f" and p.Category='{p['cat']}'"
    return c


# Złączenia faktów z wymiarami. Sprzedaż (JOIN) i zwroty (RJOIN) są zawsze liczone w OSOBNYCH zapytaniach i łączone dopiero w Pythonie:
# złączenie obu faktów w SQL mnoży wiersze i zawyża wynik.
JOIN = ("from dbo.FactSales s join dbo.DimDate d using (DateKey) join dbo.DimStore st using (StoreKey) "
        "join dbo.DimProduct p using (ProductKey)")
RJOIN = ("from dbo.FactReturns r join dbo.DimDate d using (DateKey) join dbo.DimStore st using (StoreKey) "
         "join dbo.DimProduct p using (ProductKey)")


class Baseline:
    # Kolejność decyzji w answer(): (1) poza zakresem -> odmowa; (2) „prognoza" -> narzędzie forecast; (3) metryka + okres -> szablon SQL;
    # (4) wszystko inne -> wyszukiwanie w dokumentach. Model językowy nie bierze udziału w żadnym kroku.
    name = "W1"

    def __init__(self, toolbox):
        self.tb = toolbox

    def _sql(self, sql):
        return self.tb.call("run_sql", {"sql": sql})

    def answer(self, question):
        p = parse(question)
        ql = question.lower()
        if OUT_OF_SCOPE.search(question) and not re.search(r"(sprzeda|marż|transakcj)", ql):
            return "Odmowa / brak danych: pytanie dotyczy obszaru, którego nie obsługuję (dane klientów, pogoda, konkurencja, " \
                   "wynagrodzenia, zmiany w bazie lub zatwierdzanie zadań)."
        periods = [("week", f"{y}-W{w}") for y, w in p["weeks"]] or [("day", x) for x in p["days"]] or [("month", m) for m in p["months"]]
        if "prognoz" in ql:
            return self._forecast(p)
        metric = self._metric(ql)
        if metric and periods:
            return "\n".join(self._numeric(metric, p, per) for per in periods)
        return self._docs(question)

    @staticmethod
    def _metric(ql):
        # Kolejność wzorców ma znaczenie: pierwsze trafienie wygrywa, więc szczegółowe (dostępność, wskaźnik zwrotów, marża)
        # stoją przed ogólnym „sprzedaż"; „sprzedaż brutto" przed samą „sprzedażą" (= netto wg słownika).
        for pat, m in [(r"dostępno", "avail"), (r"wskaźnik zwrot|procent zwrot", "retrate"), (r"na m", "perm2"),
                       (r"marż", "margin"), (r"transakcj|upt", "tx"), (r"udział|procent", "online_share"),
                       (r"sprzeda\w+ brutto", "gross"), (r"sprzeda", "net")]:
            if re.search(pat, ql):
                return m
        return None

    def _numeric(self, m, p, per):
        label = f"{p['store'] or 'cała firma'}{' ' + p['cat'] if p['cat'] else ''}, {per[1]}"
        w = _where(p, per)
        if m in ("net", "gross"):
            col = "NetAmount" if m == "net" else "GrossAmount"
            r = self._sql(f"select sum(s.{col}) as v {JOIN} where {w}")
            return self._one(r, f"{'Sprzedaż netto' if m == 'net' else 'Sprzedaż brutto'} {label}", "PLN", f"dbo.FactSales.{col}")
        if m == "tx":
            r = self._sql(f"select count(distinct s.TransactionNo) as t, sum(s.Quantity) as u {JOIN} where {w}")
            if r.get("ok") and r["rows"][0][0]:
                t, u = r["rows"][0]
                return f"Transakcje {label}: {t}, sztuki: {int(u)}, UPT = {fmt(u / t)} (słownik metryk: COUNT DISTINCT TransactionNo)."
        if m == "margin":
            # Marża brutto wg słownika = sprzedaż netto - koszt własny - zwroty netto (bez VAT) PRZYJĘTE w okresie: trzy wartości z dwóch zapytań.
            a = self._sql(f"select sum(s.NetAmount) as n, sum(s.Quantity*s.UnitCost) as c {JOIN} where {w}")
            b = self._sql(f"select sum(r.ReturnAmount)/1.23 as v {RJOIN} where {w}")
            if a.get("ok") and b.get("ok") and a["rows"][0][0]:
                n, c = a["rows"][0]
                rv = b["rows"][0][0] or 0
                return f"Marża brutto {label}: {fmt(n - c - rv)} PLN (sprzedaż netto {fmt(n)} − koszt własny {fmt(c)} − zwroty netto {fmt(rv)}; słownik metryk)."
        if m == "retrate":
            # Wskaźnik zwrotów = sztuki zwrócone / sztuki sprzedane w tym samym okresie i przekroju: dwa osobne zapytania, potem dzielenie.
            a = self._sql(f"select sum(s.Quantity) as v {JOIN} where {w}")
            b = self._sql(f"select sum(r.Quantity) as v {RJOIN} where {w}")
            if a.get("ok") and b.get("ok") and a["rows"][0][0]:
                return f"Wskaźnik zwrotów {label}: {fmt(100 * b['rows'][0][0] / a['rows'][0][0])}% (sztuki zwrócone / sprzedane w okresie; słownik metryk)."
        if m == "avail" and per[0] == "day":
            where = f"d.Date=DATE '{per[1]}'" + (f" and st.StoreCode='{p['store']}'" if p["store"] else "")
            r = self._sql("select 100.0*count(*) filter (where i.StockQuantity>0)/count(*) as v, count(*) as n "
                          "from dbo.FactInventoryDaily i join dbo.DimDate d using (DateKey) join dbo.DimStore st using (StoreKey) "
                          f"where {where}")
            if r.get("ok") and r["rows"][0][1]:
                return f"Dostępność {label}: {fmt(r['rows'][0][0], 1)}% (SKU ze stanem > 0 wśród SKU w feedzie; słownik metryk)."
        if m == "perm2" and p["store"] and p["store"] != "S-ONL-01":
            r = self._sql(f"select sum(s.NetAmount)/max(st.SalesAreaM2) as v {JOIN} where {w}")
            return self._one(r, f"Przychód netto na m² {label}", "PLN/m²", "dbo.FactSales.NetAmount / DimStore.SalesAreaM2 (bieżąca powierzchnia)")
        if m == "online_share" and per[0] == "month":
            r = self._sql(f"select 100.0*sum(s.NetAmount) filter (where st.Channel='ONLINE')/sum(s.NetAmount) as v {JOIN} where d.YearMonth='{per[1]}'")
            return self._one(r, f"Udział online w sprzedaży netto {per[1]}", "%", "dbo.FactSales.NetAmount, DimStore.Channel")
        return f"Brak danych / nie potrafię policzyć metryki '{m}' dla: {label}."

    @staticmethod
    def _one(r, name, unit, src):
        if r.get("ok") and r["rows"] and r["rows"][0][0] is not None:
            return f"{name}: {fmt(r['rows'][0][0])} {unit} (źródło: {src})."
        return f"{name}: brak danych."

    def _forecast(self, p):
        if not p["style"] or not p["weeks"]:
            return "Brak danych: prognoza wymaga modelu (kod stylu) i tygodnia początkowego."
        r = self.tb.call("forecast", {"start_week": f"{p['weeks'][0][0]}-W{p['weeks'][0][1]}", "n_weeks": 4,
                                      "style_code": p["style"], **({"store_code": p["store"]} if p["store"] else {})})
        if not r.get("ok"):
            return f"Nie podaję prognozy: {r.get('error')}"
        if r.get("refused"):
            return f"Nie podaję prognozy: {r['reason']}"
        rows = r["forecast_by_store"]
        return "Prognoza (szt.): " + "; ".join(f"{x['store_code']}: {fmt(x['forecast_units'], 0)} (przedział 80%: {fmt(x['low80'], 0)}–{fmt(x['high80'], 0)})" for x in rows) + f". {r['method']}."

    def _docs(self, q):
        # Wynik poniżej progu 3,0 uznajemy za brak dopasowania (BM25 zawsze coś zwróci, nawet gdy dokumentu nie ma), a nieaktualne wersje pomijamy.
        r = self.tb.call("search_docs", {"query": q, "k": 3})
        res = [x for x in r["results"] if x["score"] >= 3.0 and not x["status"].startswith("NIEAKTUALNY")]
        if not res:
            return "Brak informacji w dokumentach procedur Nordvik na ten temat."
        top = res[0]
        return f"{top['text']}\n(Źródło: {top['title']}, v{top['version']}, obowiązuje od {top['valid_from']}, sekcja „{top['section']}”.)"
