"""Dni otwarcia sklepów: święta PL i niedziele handlowe (sekcja 3 notebooka)."""

from __future__ import annotations

import holidays
import pandas as pd
from dateutil.easter import easter


def last_sunday(year: int, month: int) -> pd.Timestamp:
    end = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
    return end - pd.Timedelta(days=(end.day_of_week + 1) % 7)


def trading_sundays(year: int) -> set[pd.Timestamp]:
    # Założenie z notebooka: trzy niedziele przed Wigilią obowiązują też przed 2025 (do potwierdzenia).
    out = {last_sunday(year, m) for m in (1, 4, 6, 8)}
    out.add(pd.Timestamp(easter(year)) - pd.Timedelta(days=7))
    xmas_eve = pd.Timestamp(year, 12, 24)
    sundays_before = [xmas_eve - pd.Timedelta(days=d) for d in range(1, 30)
                      if (xmas_eve - pd.Timedelta(days=d)).day_of_week == 6]
    out.update(sundays_before[:3])
    return out


def store_calendar(start: str, end: str) -> pd.DataFrame:
    days = pd.date_range(start, end)
    years = sorted({d.year for d in days})
    hol = holidays.country_holidays("PL", years=years, language="pl")
    trading = set().union(*[trading_sundays(y) for y in years])
    cal = pd.DataFrame({"date": days})
    cal["is_holiday"] = cal.date.map(lambda d: d.date() in hol)
    cal["is_sunday"] = cal.date.dt.day_of_week == 6
    cal["trading_sunday"] = cal.date.isin(trading)
    cal["store_open"] = ~cal.is_holiday & (~cal.is_sunday | cal.trading_sunday)
    cal["week_start"] = cal.date - pd.to_timedelta(cal.date.dt.day_of_week, unit="D")
    return cal


def store_open_days(cal: pd.DataFrame) -> pd.Series:
    """Liczba dni otwarcia sklepu stacjonarnego w tygodniu ISO (indeks: poniedziałek)."""
    return cal.groupby("week_start").store_open.sum().astype(int)
