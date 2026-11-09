# SQL: Dokumentacja i przykłady zapytań

*Dokument zawiera szablony, konwencje i przykłady zapytań SQL dla zespołu Data Science w Nordvik.*

---

## Spis treści

1. [CHANGELOG](#changelog)
2. [Struktura dokumentacji SQL](#struktura-dokumentacji-sql)
3. [Przykłady zapytań SQL](#przykłady-zapytań-sql)
4. [Checklist SQL](#checklist-sql)

---

## CHANGELOG

| Data | Autor | Ticket | Model AI | Zmiana |
|------|-------|--------|----------|--------|
| 2026-11-09 | Olek | [#zgloszenia/01](../zgloszenia/01.md) | Claude 3.5 Sonnet | Dokument utworzony: szablony dokumentacji SQL + 3 przykłady zapytań (basic, intermediate, advanced) |
| | | | | |

**Format wpisu:** `YYYY-MM-DD | Imię Nazwisko | [#ticket] | Model/brak | Czego zmieniono i dlaczego w jednej linii, konkretnie**

---

## Struktura dokumentacji SQL

Każde zapytanie SQL powinno zawierać:

### 1. Nagłówek
```
-- Query Name: [Czytelna nazwa zapytania]
-- Author: [Imię, zespół]
-- Created: [Data]
-- Updated: [Data ostatniej aktualizacji]
-- Purpose: [Po co to zapytanie, co oblicza]
```

### 2. Słownie opis
```
-- Description:
-- Zapytanie oblicza średnią sprzedaż na metr kwadratowy
-- dla każdego sklepu stacjonarnego w bieżącym sezonie.
-- 
-- Uwagi: 
-- - Uwzględnia tylko transakcje ze statusem COMPLETED
-- - Pomija zwroty (negative_quantity)
-- - Powierzchnia brana z bieżącego okresu
```

### 3. Parametry
```
-- Parameters:
-- @season (varchar): kod sezonu, np. 'SS26', 'AW26' 
-- @channel (varchar): kanał sprzedaży, wartości: 'STORE', 'ONLINE'
-- @min_sales_amount (decimal): minimalna sprzedaż do filtrowania
```

### 4. Zwracane kolumny
```
-- Returns:
-- store_id (int): identyfikator sklepu
-- store_name (varchar): nazwa sklepu
-- avg_sales_per_sqm (decimal): średnia sprzedaż na m²
-- total_transactions (int): liczba transakcji
```

### 5. Załączniki
```
-- Dependencies:
-- Tables: sales.transactions, master.stores, master.seasons
-- Views: v_sales_with_store_info
-- Functions: fn_calculate_vat_amount()
```

---

## Przykłady zapytań SQL

### Przykład 1: Podstawowa analiza sprzedaży — Daily Sales Summary by Store and Channel

```sql
-- Query Name: Daily Sales Summary by Store and Channel
-- Author: Anna Kowalska, Team Data Science
-- Created: 2026-01-15
-- Updated: 2026-11-09
-- Purpose: 
-- Oblicza dzienną sprzedaż brutto i ilość transakcji dla każdego sklepu
-- i kanału. Używane do monitorowania codziennych wyników i anomalii.

-- Description:
-- Sumuje wartości sprzedaży (w PLN, bez VAT) i liczy transakcje
-- dla każdej kombinacji sklepu, kanału i dnia.
-- Filtruje tylko transakcje ze statusem COMPLETED.

-- Parameters:
-- @start_date (date): data początkowa
-- @end_date (date): data końcowa
-- @exclude_returns (bit): czy exclude negative quantities (zwroty)

-- Returns:
-- sale_date (date)
-- store_id (int)
-- store_name (varchar)
-- channel (varchar): 'STORE' lub 'ONLINE'
-- gross_sales_pln (decimal): sprzedaż brutto (bez VAT)
-- transaction_count (int)
-- avg_basket_size (decimal): średnia wartość koszyka

SELECT
    t.sale_date,
    s.store_id,
    s.store_name,
    s.channel,
    SUM(t.amount) AS gross_sales_pln,
    COUNT(DISTINCT t.transaction_id) AS transaction_count,
    AVG(t.amount) AS avg_basket_size
FROM
    sales.transactions t
    INNER JOIN master.stores s ON t.store_id = s.store_id
WHERE
    t.sale_date BETWEEN '2026-11-01' AND '2026-11-09'
    AND t.transaction_status = 'COMPLETED'
    AND (t.quantity > 0 OR 1 = 0)  -- wyklucza zwroty gdy @exclude_returns = 1
GROUP BY
    t.sale_date,
    s.store_id,
    s.store_name,
    s.channel
ORDER BY
    t.sale_date DESC,
    gross_sales_pln DESC;

-- Notes:
-- • Sprzedaż to value_before_discount, bez uwzględniania VAT
-- • Zwroty to transakcje z quantity < 0, rozważ ich osobne liczenie
-- • Dla ONLINE może być opóźnienie w danych (up to 2h SLA)
-- • Wykres dobrze się rysuje za ostatnie 30 dni
```

---

### Przykład 2: Średniozaawansowana analiza — Sales Performance by Product Category

```sql
-- Query Name: Season Performance by Product Category and Size
-- Author: Piotr Lewandowski, Team Data Science
-- Created: 2026-10-22
-- Updated: 2026-11-08
-- Purpose:
-- Analiza sprzedaży i zwrotów w podziale na kategorie produktów i rozmiary.
-- Identify bestsellers i produkty problemowe (high return rate).

-- Description:
-- Grupuje sprzedaż (bez VAT) i zwroty netto (quantity < 0) po kategoriach
-- i rozmiarach. Oblicza ROI na podstawie kosztu pozyskania towaru.
-- Return rate = zwroty / sprzedane sztuki.

-- Parameters:
-- @season (varchar): kod sezonu, np. 'SS26', 'AW26'
-- @min_qty_sold (int): minimalny próg ilości do uwzględnienia (default 50)
-- @return_rate_threshold (decimal): próg return rate do flagowania, np. 0.10

-- Returns:
-- category (varchar)
-- size_code (varchar)
-- quantity_sold (int)
-- quantity_returned (int)
-- return_rate (decimal): % zwrotów
-- total_sales_pln (decimal)
-- total_cost_pln (decimal)
-- gross_margin_pct (decimal)
-- net_roi (decimal): zysk netto / koszt pozyskania

SELECT
    pc.product_category,
    p.size_code,
    SUM(CASE WHEN t.quantity > 0 THEN t.quantity ELSE 0 END) AS quantity_sold,
    SUM(CASE WHEN t.quantity < 0 THEN ABS(t.quantity) ELSE 0 END) AS quantity_returned,
    CAST(
        SUM(CASE WHEN t.quantity < 0 THEN ABS(t.quantity) ELSE 0 END) * 100.0 /
        NULLIF(SUM(CASE WHEN t.quantity > 0 THEN t.quantity ELSE 0 END), 0)
        AS DECIMAL(5, 2)
    ) AS return_rate_pct,
    SUM(CASE WHEN t.quantity > 0 THEN t.amount ELSE 0 END) AS total_sales_pln,
    SUM(p.cost_unit_pln * t.quantity) AS total_cost_pln,
    CAST(
        (SUM(CASE WHEN t.quantity > 0 THEN t.amount ELSE 0 END) - 
         SUM(p.cost_unit_pln * ABS(t.quantity))) * 100.0 /
        NULLIF(SUM(CASE WHEN t.quantity > 0 THEN t.amount ELSE 0 END), 0)
        AS DECIMAL(5, 2)
    ) AS gross_margin_pct
FROM
    sales.transactions t
    INNER JOIN master.products p ON t.product_id = p.product_id
    INNER JOIN master.product_categories pc ON p.category_id = pc.category_id
WHERE
    p.season_code = 'SS26'
    AND t.transaction_status = 'COMPLETED'
GROUP BY
    pc.product_category,
    p.size_code
HAVING
    SUM(CASE WHEN t.quantity > 0 THEN t.quantity ELSE 0 END) >= 50
ORDER BY
    return_rate_pct DESC,
    total_sales_pln DESC;

-- Notes:
-- • Kategoria produktu pochodzi z hierarchii master.product_categories
-- • Kostlabor musi być uzupełniony w master.products (nullable!)
-- • Return rate powyżej 15% dla ONLINE jest norma, dla STORE > 8% to anomalia
-- • Margines obliczany PRZED rabatami (wartość sprzedaży = price_after_discount)
-- • Zwroty liczą się ujemnie w quantity, mogą mieć odrębne KOD_PRZYCZYNY
```

---

### Przykład 3: Zaawansowana analiza — Cohort Analysis for Customer Retention

```sql
-- Query Name: Customer Retention Cohort Analysis
-- Author: Maria Nowak, Team Analytics
-- Created: 2026-09-20
-- Updated: 2026-11-05
-- Purpose:
-- Analiza retention rate dla kohort klientów (grupy nabyte w tym samym miesiącu).
-- Identyfikuje trendy w loyal ty i lifetime value.

-- Description:
-- Tworzy kohorty na podstawie miesiąca pierwszego zakupu.
-- Dla każdej kohorty liczy procent klientów, którzy wrócili w kolejnych miesiącach.
-- Uwzględnia zarówno zakupy w sklepach jak i online.

-- Parameters:
-- @cohort_start_month (varchar): np. '2026-02' (format YYYY-MM)
-- @cohort_end_month (varchar): np. '2026-09'
-- @min_initial_purchase_pln (decimal): minimalna wartość pierwszego zakupu (default 0)

-- Returns:
-- cohort_month (varchar): miesiąc pierwszego zakupu
-- cohort_size (int): liczba unikatowych klientów w kohorcie
-- month_0, month_1, month_2, ... : % retention w n-tym miesiącu

-- CTE (Common Table Expressions):

WITH customer_first_purchase AS (
    -- Każdy klient + miesiąc jego pierwszego zakupu
    SELECT
        t.customer_id,
        DATEFROMPARTS(YEAR(MIN(t.sale_date)), MONTH(MIN(t.sale_date)), 1) AS first_purchase_date,
        SUM(t.amount) AS first_purchase_amount
    FROM
        sales.transactions t
    WHERE
        t.transaction_status = 'COMPLETED'
        AND t.quantity > 0
    GROUP BY
        t.customer_id
),
customer_monthly_activity AS (
    -- Każdy klient + miesiąc aktywności (czy zakupił w tym miesiącu)
    SELECT
        cfp.customer_id,
        cfp.first_purchase_date,
        DATEFROMPARTS(YEAR(t.sale_date), MONTH(t.sale_date), 1) AS activity_month
    FROM
        customer_first_purchase cfp
        LEFT JOIN sales.transactions t ON cfp.customer_id = t.customer_id
            AND t.transaction_status = 'COMPLETED'
            AND t.quantity > 0
            AND t.sale_date >= cfp.first_purchase_date
    WHERE
        cfp.first_purchase_date >= '2026-02-01'
        AND cfp.first_purchase_amount >= 0
    GROUP BY
        cfp.customer_id,
        cfp.first_purchase_date,
        DATEFROMPARTS(YEAR(t.sale_date), MONTH(t.sale_date), 1)
),
cohort_analysis AS (
    -- Pivot: dla każdej kohorty, % klientów aktywnych w каждym месяце
    SELECT
        FORMAT(cfp.first_purchase_date, 'yyyy-MM') AS cohort_month,
        COUNT(DISTINCT cfp.customer_id) AS cohort_size,
        COUNT(DISTINCT CASE WHEN DATEDIFF(MONTH, cfp.first_purchase_date, cma.activity_month) = 0 THEN cfp.customer_id END) * 100.0 / NULLIF(COUNT(DISTINCT cfp.customer_id), 0) AS month_0,
        COUNT(DISTINCT CASE WHEN DATEDIFF(MONTH, cfp.first_purchase_date, cma.activity_month) = 1 THEN cfp.customer_id END) * 100.0 / NULLIF(COUNT(DISTINCT cfp.customer_id), 0) AS month_1,
        COUNT(DISTINCT CASE WHEN DATEDIFF(MONTH, cfp.first_purchase_date, cma.activity_month) = 2 THEN cfp.customer_id END) * 100.0 / NULLIF(COUNT(DISTINCT cfp.customer_id), 0) AS month_2,
        COUNT(DISTINCT CASE WHEN DATEDIFF(MONTH, cfp.first_purchase_date, cma.activity_month) = 3 THEN cfp.customer_id END) * 100.0 / NULLIF(COUNT(DISTINCT cfp.customer_id), 0) AS month_3
    FROM
        customer_first_purchase cfp
        LEFT JOIN customer_monthly_activity cma ON cfp.customer_id = cma.customer_id
    GROUP BY
        FORMAT(cfp.first_purchase_date, 'yyyy-MM')
)
SELECT
    cohort_month,
    cohort_size,
    CAST(month_0 AS DECIMAL(5, 1)) AS month_0_pct,
    CAST(month_1 AS DECIMAL(5, 1)) AS month_1_pct,
    CAST(month_2 AS DECIMAL(5, 1)) AS month_2_pct,
    CAST(month_3 AS DECIMAL(5, 1)) AS month_3_pct
FROM
    cohort_analysis
ORDER BY
    cohort_month;

-- Notes:
-- • Month_0 zawsze będzie ~100% (klient zaraz po pierwszym zakupie)
-- • Retention rate typowo spada: 100% → 35-50% → 20-30% → 15-20%
-- • Kohorty utworzone < 3 miesiące temu będą niekompletne
-- • Customer_id może być NULL dla anonymous checkout (ONLINE kanał)
-- • Anomalia: retention nagle > 100% = bug w danych, sprawdź dla tego miesiąca
```

---

## Checklist SQL

Zanim udostępnisz zapytanie innemu członkowi zespołu, przejdź przez poniższy checklist:

### Dokumentacja

- [ ] **Nagłówek:**
  - [ ] Nazwa zapytania jest opisowa i zaczyna się od czasownika (np. "Calculate Sales by...") lub rzeczownika (np. "Customer Retention Cohort")
  - [ ] Wpisany autor i data
  - [ ] Purpose wyjaśnia biznesowy cel, nie tylko to co SQL robi
  
- [ ] **Opis:**
  - [ ] Description wyjaśnia, co zapytanie oblicza w prosty sposób
  - [ ] Listed all important parameters with types
  - [ ] Zwracane kolumny opisane (nazwy i znaczenie)
  - [ ] Dependencies (tabele, widoki, funkcje) wymienione

### Kod SQL

- [ ] **Testy i wydajność:**
  - [ ] Zapytanie wykonuje się bez błędów
  - [ ] Czas wykonania < 30 sec (lub zaznaczono, że to "long-running")
  
- [ ] **Czytelność kodu:**
  - [ ] Nazwy kolumn w SELECT są czytelne (nie `t1.col_x`, ale `transaction_date`, `store_name`)
  - [ ] WHERE conditions jasne i nie zawierają hardcoded wartości (użyj parametrów lub zakomentuj wartości)
  - [ ] JOINy są INNER/LEFT/RIGHT, a nie CROSS
  - [ ] Brak `SELECT *` — wymienione dokładnie które kolumny
  - [ ] CTEs (WITH clause) są używane, jeśli zapytanie jest długie (> 100 linii)

- [ ] **Notatki (Notes):**
  - [ ] Opisane wszelkie "pułapki" (np. "return rate powyżej 15% jest norma dla ONLINE")
  - [ ] Wymienione, jakie były zmiany danych / kiedy raport został ostatnio update'owany
  - [ ] Jeśli dane mogą być NULL, opisane konsekwencje (czy to bug czy feature?)

---

## Wskazówki komunikacyjne

**Gdy widzisz kod bez dokumentacji:**

```
❌ "To mi się nie podoba, dokumentacja to gówno"

✅ "Hej, moglibyśmy dodać nagłówek z Purpose? Wtedy będzie jasne po co
   to zapytanie i kto go ostatnio update'ował. Mogę pomóc jeśli chcesz."
```

**Gdy zapytanie jest wolne:**

```
❌ "To zapytanie to wąskie gardło"

✅ "Zaobserwowaliśmy, że to zapytanie wykonuje się 45 sec.
   Czy się używa? Jeśli tak, mogę zaproponować indeksy na:
   - sales.transactions(sale_date)
   - master.stores(store_id)
   Lub moglibyśmy cachować wynik?"
```

---

*Wersja 1.0 — Nordvik Data Science Team — 2026-11-09*
