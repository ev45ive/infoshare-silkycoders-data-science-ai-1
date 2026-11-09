# Lineage: sprzedaż po korektach

## 1. Tabela lineage

| Pole biznesowe | Kolumna techniczna | Raport/widok | Transformacja/formuła | Źródło | Ziarno | Wersja/czas | Dowód / niewiadoma |
|---|---|---|---|---|---|---|---|
| sprzedaż po korektach | `reporting.vw_SalesAfterAdjustments.SalesAfterAdjustments` | `reporting.vw_SalesAfterAdjustments` | sprzedaż `COMPLETED` + korekty `POSTED` | `FactSales` + `FactAdjustment` | sklep × ISO tydzień | REL-2026.10.3 (13.10.2026 17:20); katalog CAT-2026.10 (14.10.2026 08:00) | [implementacja.sql](/home/teamsharq/Desktop/infoshare-silkycoders-data-science-ai-1/zgloszenia/E02-B/implementacja.sql) |
| sprzedaż po korektach — zwroty | brak w widoku | `dbo.FactReturns` | nieodejmowane (brak joinu) | `dbo.FactReturns` | pozycja zwrotu | REL-2026.10.3 | komentarz w `implementacja.sql`; w próbce 36 907,00 |
| sprzedaż po korektach — legacy | `reporting.vw_WeeklySalesLegacy` | obiekt wycofany | tydzień kalendarzowy, nie ISO | nieznane | sklep × tydzień kalendarzowy | emerytowany wg katalogu | [katalog.md](/home/teamsharq/Desktop/infoshare-silkycoders-data-science-ai-1/zgloszenia/E02-B/katalog.md); niewiadoma: czy zestawienie go używa |
| sprzedaż po korektach — alias | `reporting.vw_SalesAdjusted` | nieznany | nieznana | nieznane | nieznane | brak w eksporcie | niewiadoma: brak definicji |

### Łańcuch źródeł

- **Sprzedaż:** `src.SalesRaw` → `stg.Sales` → `dbo.FactSales`
- **Korekty:** `src.AdjustmentRaw` → `stg.Adjustment` → `dbo.FactAdjustment`
- **Dowody ETL:** [staging_fact.sql](/home/teamsharq/Desktop/infoshare-silkycoders-data-science-ai-1/zgloszenia/E02-B/staging_fact.sql), [adjustment_lineage.sql](/home/teamsharq/Desktop/infoshare-silkycoders-data-science-ai-1/zgloszenia/E02-B/adjustment_lineage.sql)

## 2. Komunikat dla controllingu

### Ustalone fakty

- Pole pochodzi z `reporting.vw_SalesAfterAdjustments` (REL-2026.10.3).
- Formuła: suma `Quantity × UnitNetPrice` dla `COMPLETED` + suma `AdjustmentAmount` dla `POSTED`, per sklep i ISO tydzień.
- Próbka (`przyklad_wierszy.csv`, 3 705 wierszy, dane syntetyczne):
  - suma wszystkich pozycji sprzedaży: **934 524,00**
  - anulowane (`CANCELLED`, 125 poz.): **−38 051,00**
  - `COMPLETED`: **896 473,00**
  - korekty `POSTED` (DRAFT, 42 wiersze, wykluczone): **+84,34**
  - wynik widoku: **896 557,34**
- Zwroty (`FactReturns`) w próbce: 36 907,00, nieodejmowane w widoku.
- Load log RUN-26014: 12 odczytanych, 10 załadowanych, 2 odrzucone (`RejectedSales`).
- Jedna korekta `POSTED` (23,83) nie ma sprzedaży `COMPLETED` w tym samym sklepie i tygodniu, więc LEFT JOIN ją gubi.

### Hipotezy do sprawdzenia

- Różnica względem „sumy paragonów” wynika najpewniej z anulowanych pozycji (38 051) i pominięcia zwrotów (36 907). Potwierdzić, jak controlling liczy paragony.
- Możliwe przypisanie do innego tygodnia, jeśli zestawienie używa `vw_WeeklySalesLegacy` (tydzień kalendarzowy). Sprawdzić źródło zestawienia.
- Możliwa cicha utrata wierszy: `TRY_CONVERT` daje NULL, a INNER JOIN do wymiarów odrzuca wiersz bez wpisu w `LoadLog`. Porównać liczby wierszy `src` → `stg` → `Fact`.
- Znak korekt: w próbce 159 ujemnych wartości. Potwierdzić, że źródło podaje znak zgodny z definicją.

### Braki i granice wniosku

- Próbka jest syntetyczna i nie pokazuje skali różnicy w produkcyjnym zestawieniu.
- Brak definicji „sumy paragonów” i zapytania zestawienia tygodniowego.
- `vw_SalesAdjusted` nie został zweryfikowany (brak w eksporcie schematu).
- Brak liczników odrzuceń z pełnych ładowań.

### Krótka odpowiedź

- Liczba pochodzi z `vw_SalesAfterAdjustments`: sprzedaż `COMPLETED` + korekty `POSTED`.
- Różnica od paragonów wynika z definicji, nie z błędu wartości: widok pomija zwroty, uwzględnia tylko pozycje `COMPLETED` i gubi korekty bez sprzedaży w tym tygodniu.
- Przed zamknięciem: potwierdzić definicję „sumy paragonów” i sprawdzić, czy zestawienie nie używa obiektu legacy.

## 3. Diagramy

**Legenda**
- linia ciągła `-->` — potwierdzone w SQL
- linia przerywana `-.->` — niewiadoma lub element spoza wyniku widoku

### 3.1 Lineage

```mermaid
flowchart LR
  SR["src.SalesRaw"] --> SS["stg.Sales"]
  SS --> FS["dbo.FactSales"]
  FS --> V["reporting.vw_SalesAfterAdjustments"]
  AR["src.AdjustmentRaw"] --> SA["stg.Adjustment"]
  SA --> FA["dbo.FactAdjustment"]
  FA --> V
  FR["dbo.FactReturns"] -.->|"brak joinu w widoku"| V
  V -.->|"niewiadoma: używany w zestawieniu?"| LG["reporting.vw_WeeklySalesLegacy"]
  AL["reporting.vw_SalesAdjusted"] -.->|"niewiadoma: brak w eksporcie"| V
```

*Źródło liczb: diagram pokazuje ścieżki z definicji obiektów (`implementacja.sql`, `staging_fact.sql`, `adjustment_lineage.sql`), bez wartości z próbki.*

### 3.2 Mostek kwot

```mermaid
flowchart LR
  T["Suma wszystkich pozycji<br/>934 524,00"] -->|"anulowane −38 051,00"| C["COMPLETED<br/>896 473,00"]
  C -->|"korekty POSTED +84,34"| W["SalesAfterAdjustments<br/>896 557,34"]
  DR["Korekty DRAFT<br/>42 wiersze, wykluczone"] -.->|"poza definicją"| W
  Z["Zwroty FactReturns<br/>36 907,00, nieodjęte"] -.->|"poza definicją"| W
```

*Źródło liczb: sumy z próbki [przyklad_wierszy.csv](/home/teamsharq/Desktop/infoshare-silkycoders-data-science-ai-1/zgloszenia/E02-B/przyklad_wierszy.csv) (dane syntetyczne), wyliczone wg formuły widoku.*
