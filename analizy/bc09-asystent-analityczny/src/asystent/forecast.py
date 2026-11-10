"""Narzędzie `forecast`: prosty, jawny model sezonowy z przedziałem z backtestu.

Model (na serię = model produktu x lokalizacja):
    prognoza(tygodnie H) = SUMA sprzedaży sztuk z tych samych tygodni ISO roku poprzedniego
                           x (sztuki z ostatnich 8 pełnych tygodni / sztuki z tych samych 8 tygodni roku poprzedniego)
Przedział 80%: kwantyle 10% i 90% względnego błędu (rzeczywiste/prognoza - 1) z backtestu tej samej metody
na oknach 4-tygodniowych w 2026 r., łączonych po wszystkich seriach. Dla sum (kategoria, wszystkie sklepy) granice
są sumą granic serii (zachowawczo: nie zakładamy kompensowania się błędów).
Odmowa (bez liczby), gdy model nie ma historii obejmującej okno referencyjne roku poprzedniego.
"""
import json
import re

import numpy as np
import pandas as pd

from . import config

WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
MAX_HORIZON_WEEKS = 8
RECENT_WEEKS = 8


def parse_week(s):
    m = WEEK_RE.match(str(s).strip())
    if not m:
        raise ValueError(f"Tydzień musi mieć format RRRR-Wnn (np. 2026-W39), otrzymano: {s!r}")
    return int(m.group(1)), int(m.group(2))


def week_monday(y, w):
    return pd.Timestamp.fromisocalendar(y, w, 1)


def week_index(y, w):
    """Ciągły numer tygodnia (do arytmetyki na tygodniach)."""
    return (week_monday(y, w) - pd.Timestamp("2000-01-03")).days // 7


def index_to_week(i):
    d = pd.Timestamp("2000-01-03") + pd.Timedelta(weeks=int(i))
    iso = d.isocalendar()
    return int(iso.year), int(iso.week)


class Forecaster:
    def __init__(self, con):
        self.con = con
        df = con.execute("""
            select p.StyleCode, p.Category, st.StoreCode, d.IsoYear, d.IsoWeek, sum(s.Quantity) as units
            from dbo.FactSales s join dbo.DimDate d using (DateKey) join dbo.DimProduct p using (ProductKey)
            join dbo.DimStore st using (StoreKey)
            group by all""").df()
        df["widx"] = [week_index(y, w) for y, w in zip(df.IsoYear, df.IsoWeek)]
        self.weekly = df
        last_day, = con.execute("select max(d.Date) from dbo.FactSales s join dbo.DimDate d using (DateKey)").fetchone()
        last_day = pd.Timestamp(last_day)
        iso = last_day.isocalendar()
        # Ostatni PEŁNY tydzień ISO: gdy dane kończą się w niedzielę, ten tydzień jest pełny; w przeciwnym razie cofamy się o tydzień.
        self.last_full_widx = week_index(iso.year, iso.week) - (0 if last_day.isoweekday() == 7 else 1)
        self.first_sale = {r.StyleCode: r.d for r in con.execute(
            "select p.StyleCode, min(d.Date) d from dbo.FactSales s join dbo.DimDate d using (DateKey) "
            "join dbo.DimProduct p using (ProductKey) group by 1").df().itertuples()}
        self._series = {k: g.set_index("widx")["units"] for k, g in df.groupby(["StyleCode", "StoreCode"])}
        self._cat = df.groupby("StyleCode")["Category"].first().to_dict()
        self._q = None

    # --- rdzeń: jedna seria ---------------------------------------------------------------
    def _units(self, key, a, b):
        s = self._series.get(key)
        if s is None:
            return 0.0
        return float(s.reindex(range(a, b + 1)).fillna(0).sum())

    def _point(self, key, h0, n, origin):
        """Prognoza punktowa dla tygodni [h0, h0+n-1] z punktem odcięcia `origin` (ostatni znany pełny tydzień)."""
        # Wzór: prognoza = sprzedaż z tych samych tygodni rok temu x (poziom ostatnich 8 tygodni / poziom tych samych 8 tygodni rok temu).
        # Pierwszy czynnik daje kształt sezonowy, drugi skaluje go do bieżącego poziomu sprzedaży. Bez historii sprzed roku (recent_ly = 0) nie ma prognozy.
        r0 = origin - RECENT_WEEKS + 1
        ly = 52  # przesunięcie o rok = 52 tygodnie; tydzień 53 roku 2026 nie wpływa na okno W31..W42
        last_year_h = self._units(key, h0 - ly, h0 - ly + n - 1)
        recent = self._units(key, r0, origin)
        recent_ly = self._units(key, r0 - ly, origin - ly)
        if recent_ly <= 0:
            return None
        return last_year_h * recent / recent_ly

    def _backtest_quantiles(self):
        if self._q is not None:
            return self._q
        # Backtest: dla każdej serii (model x sklep) i każdego punktu odcięcia w 2026 liczymy prognozę 4-tygodniową i porównujemy z faktem.
        # Kwantyle 10% i 90% względnego błędu (rzeczywiste/prognoza - 1) tworzą przedział 80%. Wynik jest deterministyczny, więc cache'owany w pliku.
        cache = config.CACHE / "forecast_backtest.json"
        if cache.exists():
            self._q = json.loads(cache.read_text())
            return self._q
        errs = []
        for key in self._series:
            first = self.first_sale[key[0]]
            for origin in range(week_index(2026, 9) - 1, self.last_full_widx - 3):
                h0 = origin + 1
                need_from = week_monday(*index_to_week(origin - RECENT_WEEKS + 1 - 52))
                if first > need_from:
                    continue
                f = self._point(key, h0, 4, origin)
                a = self._units(key, h0, h0 + 3)
                if f and f > 0:
                    errs.append(a / f - 1)
        e = np.array(errs)
        self._q = {"n": int(len(e)), "q10": float(np.quantile(e, 0.10)), "q90": float(np.quantile(e, 0.90)),
                   "median": float(np.median(e))}
        config.CACHE.mkdir(exist_ok=True)
        cache.write_text(json.dumps(self._q))
        return self._q

    # --- API narzędzia --------------------------------------------------------------------
    def forecast(self, start_week, n_weeks=4, style_code=None, category=None, store_code=None):
        """Zwraca słownik: ok, refused/reason, wiersze per sklep (i model) z przedziałem."""
        try:
            y, w = parse_week(start_week)
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        n = int(n_weeks)
        h0 = week_index(y, w)
        origin = self.last_full_widx
        if not (1 <= n <= MAX_HORIZON_WEEKS):
            return {"ok": False, "error": f"n_weeks musi być w zakresie 1..{MAX_HORIZON_WEEKS} (tylko prognozy tygodniowe)."}
        if h0 <= origin or h0 > origin + MAX_HORIZON_WEEKS:
            ly, lw = index_to_week(origin)
            return {"ok": False, "error": f"start_week musi wypadać w ciągu {MAX_HORIZON_WEEKS} tygodni po ostatnim pełnym "
                                          f"tygodniu danych ({ly}-W{lw:02d}). Narzędzie nie prognozuje pojedynczych dni."}
        if not style_code and not category:
            return {"ok": False, "error": "Podaj style_code (model) albo category."}
        styles = [style_code] if style_code else sorted(k for k, c in self._cat.items() if c == category)
        if not styles or any(s not in self._cat for s in styles):
            return {"ok": False, "error": "Nieznany model lub kategoria."}
        stores = [store_code] if store_code else sorted({k[1] for k in self._series})
        q = self._backtest_quantiles()
        rows, excluded = [], []
        for s in styles:
            first = self.first_sale[s]
            need_from = week_monday(*index_to_week(origin - RECENT_WEEKS + 1 - 52))
            if first > need_from:
                # Odmowa z powodem: model bez historii z okna referencyjnego sprzed roku nie ma na czym oprzeć sezonowości.
                excluded.append({"style_code": s, "reason": f"brak historii: pierwsza sprzedaż {pd.Timestamp(first).date()}, a okno "
                                 f"referencyjne roku poprzedniego zaczyna się {need_from.date()}; model sezonowy nie ma na czym się oprzeć"})
                continue
            for st in stores:
                f = self._point((s, st), h0, n, origin)
                if f is None:
                    excluded.append({"style_code": s, "store_code": st, "reason": "brak sprzedaży w oknie referencyjnym roku poprzedniego"})
                    continue
                rows.append({"style_code": s, "store_code": st, "forecast_units": round(f, 1),
                             "low80": round(f * (1 + q["q10"]), 1), "high80": round(f * (1 + q["q90"]), 1)})
        if not rows:
            return {"ok": True, "refused": True, "reason": "; ".join(e["reason"] for e in excluded[:3]),
                    "excluded": excluded, "forecast_rows": []}
        # Sumy po modelach (kategoria) i sklepach: przedziały serii DODAJEMY (zachowawczo: nie zakładamy, że błędy się wzajemnie kompensują).
        df = pd.DataFrame(rows)
        by_store = df.groupby("store_code")[["forecast_units", "low80", "high80"]].sum().round(1).reset_index()
        yh, wh = index_to_week(h0 + n - 1)
        return {"ok": True, "refused": False, "weeks": f"{y}-W{w:02d}..{yh}-W{wh:02d}",
                "method": "sezonowa średnia z roku poprzedniego x poziom ostatnich 8 pełnych tygodni; przedział 80% z backtestu "
                          f"(n={q['n']}, względny błąd {q['q10']:+.0%}..{q['q90']:+.0%})",
                "forecast_by_store": by_store.to_dict("records"),
                "forecast_rows": rows if (style_code or len(rows) <= 40) else rows[:40],
                "excluded": excluded}
