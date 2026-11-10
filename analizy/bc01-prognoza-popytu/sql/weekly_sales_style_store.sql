/*
Query Name : weekly_sales_style_store
Author     : agent AI (materiał szkoleniowy)
Created    : 2026-11-10
Updated    : 2026-11-10
Purpose    : Tygodniowa sprzedaż (sztuki, sprzedaż netto, wartość przed rabatem, rabat, liczba pozycji)
             na poziomie model (StyleCode) x lokalizacja (StoreKey) w tygodniach ISO.
Parameters : $start_date (włącznie), $end_date (wyłącznie)
Sources    : fact_sales, dim_date, dim_product (słownik metryk Nordvik: sztuki = SUM(Quantity),
             sprzedaż netto = SUM(NetAmount), wartość przed rabatem = SUM(Quantity * UnitPrice),
             stopa rabatu = SUM(DiscountAmount) / SUM(Quantity * UnitPrice))
*/
SELECT
    DATE_TRUNC('week', d."Date")::DATE      AS week_start,      -- poniedziałek tygodnia ISO
    d.IsoYear                                AS iso_year,
    d.IsoWeek                                AS iso_week,
    p.StyleCode                              AS style_code,
    f.StoreKey                               AS store_key,
    SUM(f.Quantity)                          AS qty,
    SUM(f.NetAmount)                         AS net_sales,
    SUM(f.Quantity * f.UnitPrice)            AS list_value,
    SUM(f.DiscountAmount)                    AS discount,
    COUNT(*)                                 AS n_lines
FROM fact_sales AS f
JOIN dim_date    AS d ON d.DateKey    = f.DateKey
JOIN dim_product AS p ON p.ProductKey = f.ProductKey
WHERE d."Date" >= $start_date
  AND d."Date" <  $end_date
GROUP BY
    DATE_TRUNC('week', d."Date")::DATE,
    d.IsoYear,
    d.IsoWeek,
    p.StyleCode,
    f.StoreKey;

-- Notes:
-- * Brak wiersza w wyniku NIE oznacza zera popytu: sklep mógł być zamknięty, model jeszcze nie wprowadzony lub
--   wygaszony, albo zabrakło towaru. Reguły uzupełniania zerami są w notebooku (po audycie kalendarza i premier).
-- * Grupowanie po IsoYear + IsoWeek (nie Year + IsoWeek): tydzień 2025-W01 zaczyna się 2024-12-30, a dane od 2025-01-01,
--   więc pierwszy tydzień jest niepełny (środa-niedziela).
-- * Zwroty nie są częścią wyciągu: to sprzedaż przed zwrotami, nie popyt "netto po zwrotach".
-- * UnitPrice = cena przed rabatem (brutto), NetAmount = netto po rabacie (bez VAT) - nie mieszać z list_value (z VAT).
