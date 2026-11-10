# P01.04 — Podsumowanie importów partnera: inwarianty i warianty

## Zakres odczytu

Nie zmieniano plików źródłowych. Odczytano:
- `partner_shipments_v3.xlsx`: 24 000 wierszy danych, nagłówek w wierszu 3, dane od wiersza 4.
- `partner_availability_v2.xlsx`: 24 000 wierszy danych, nagłówek w wierszu 3, dane od wiersza 4.
- `nordvik_assortment_map.csv`: 120 wierszy.

Wiersz 2 obu plików zawiera adnotację „generated example, not market evidence”, więc dane traktowane są jako syntetyczne.
Pliki znajdują się w katalogu `zgloszenia/P01-04/`. Skrypt `starter.py` szuka ich w podkatalogu `partner/`, którego nie ma.

## Inwarianty (stałe przy kolejnych importach)

### Model: shipments (`partner_shipments_v3`)

- Grain: jedna linia = `PartnerLineId` (unikalny, 0 duplikatów).
- Klucz biznesowy: `PartnerSKU` × `Destination` × `WeekStart` (24 000 unikalnych kombinacji).
- Kolumny: `PartnerLineId`, `PartnerBrand`, `PartnerSKU`, `Destination`, `WeekStart`, `UnitsBooked`, `PromisedDate`, `Status`, `PartnerNote`.
- `UnitsBooked` jest przepływem, więc sumuje się w czasie.
- `WeekStart` to poniedziałek. Wartości 46300–46321 odpowiadają 2026-10-05, 2026-10-12, 2026-10-19, 2026-10-26.
- `PromisedDate` nie jest wcześniejsza niż `WeekStart` (0 przypadków).
- `Status` przyjmuje `confirmed` lub `at_risk`. `at_risk` nie oznacza anulowania.

### Model: availability (`partner_availability_v2`)

- Grain: jedna migawka = `SnapshotId` (unikalny).
- Klucz biznesowy: `PartnerSKU` × `Destination` × `AsOfDate`.
- Kolumny: `SnapshotId`, `PartnerBrand`, `PartnerSKU`, `Destination`, `AsOfDate`, `AvailableUnits`, `ReservedUnits`, `MOQ`, `AvailabilityNote`.
- `AvailableUnits` jest stanem migawki i nie sumuje się po tygodniach.
- Dostępność netto = `AvailableUnits` − `ReservedUnits`. Partner wskazuje, że przy planowaniu liczy się wartość po rezerwacjach.
- `MOQ` przyjmuje wartości 24 lub 48.

### Mapowanie (`nordvik_assortment_map.csv`)

- Klucz: `PartnerSKU` → `NordvikSKUCode`, relacja 1:1 (120 wierszy, 120 unikalnych kodów).
- Sezon: wyłącznie `AW26`.
- Marki: `PartnerLabel-01` (100 SKU), `PartnerLabel-02` (20 SKU).
- Zgodność marki z danymi: 0 niezgodności w obu plikach dla mapowanych SKU.
- Łączenie wyłącznie przez `PartnerSKU`. Nie używać nazwy marki ani `PartnerLineId` jako klucza łączenia.

### Wspólne dla obu plików

- Te same 1 000 `PartnerSKU`.
- 6 destynacji: `Store-01` … `Store-05`, `ONLINE`.
- 10 marek.
- 4 tygodnie.
- Każdy SKU występuje w pełnej siatce SKU × destynacja × tydzień.
- Metadane w wierszach 1–2 i nagłówek w wierszu 3 należy walidować przed czytaniem.

## Czytanie, ładowanie, normalizacja

1. Czytać arkusz `Partner export` po nazwie, nie po indeksie. Sprawdzać nagłówek w wierszu 3 względem oczekiwanego schematu. Zmiana nagłówka zatrzymuje import.
2. Daty przychodzą jako numery seryjne Excela. Konwersja: `date = 1899-12-30 + n` dni. Jeśli kolejny plik przyśle `datetime`, obsłużyć oba typy.
3. Normalizacja: `strip()` na tekstach, typy liczbowe, unikalność po ID, walidacja enumów `Status`. Surowe wartości nie są nadpisywane; wartości netto zapisywać jako dodatkowe kolumny.
4. Liczniki problemów (duplikaty, braki, wartości ujemne) zapisywać jako kontrolę jakości, nie ukrywać ich.
5. Mapowanie: łączyć przez `PartnerSKU`. Wiersze bez mapy trafiają do osobnego zestawienia „niezmapowane”.

## Warianty (co może się zmienić)

- Liczba tygodni, migawek i destynacji (obecnie 4 tygodnie, 5 sklepów + ONLINE).
- Liczba SKU i zakres mapowania (obecnie 120 z 1 000 SKU zmapowanych, czyli 12%).
- Sezon (obecnie wyłącznie AW26; mogą pojawić się SS).
- Nowe wartości `Status` lub `MOQ`, nowe formaty dat.
- Braki i wartości niepoprawne (opisane niżej).
- Zmiana nazwy arkusza lub przesunięcie nagłówka.

## Pułapki i problemy w danych

- Tylko 120 z 1 000 `PartnerSKU` ma mapowanie. Wyniki dla Nordvik można policzyć wyłącznie dla tej części.
- Mapowanych wierszy w shipments jest 2 879 zamiast oczekiwanych 2 880 (120 SKU × 6 destynacji × 4 tygodnie). Brak `PartnerSKU` dotyczy wiersza `L0002010`, brak `PromisedDate` wiersza `L0005003`. Nie ustalono jeszcze, który z nich wypadał w zakresie mapowanych SKU.
- Brak `MOQ` w jednym wierszu availability (`S0002007`).
- Dostępność netto jest ujemna w 3 026 wierszach ogółem, w tym 375 dla mapowanych SKU. Nie ustalono, czy klipować do 0.
- 706 mapowanych wierszy ma dostępność netto poniżej MOQ. Nie ustalono, czy MOQ dotyczy linii, czy zamówienia.
- 319 mapowanych linii ma status `at_risk`.
- Notatka `L0004025` zawiera otwarte pytanie: „Does booked quantity include cartons awaiting final pick? Please confirm.” Wymaga wyjaśnienia definicji.
- `PartnerNote` i `AvailabilityNote` to ręczne, niestrukturalne teksty. Numer `ref` nie jest stabilnym identyfikatorem zewnętrznym.
- `AsOfDate` (migawka) i `PromisedDate` (obietnica w chwili eksportu) dotyczą różnych momentów. Partner zaznacza, że pliki nie muszą być generowane w tym samym czasie.

### Problemy w `starter.py`

- Ścieżka `partner/` nie istnieje w workspace.
- `date_value.date()` zakłada typ `datetime`, a dane mają liczby seryjne.
- Sumowanie `AvailableUnits` po tygodniach jest nieadytywne (skrypt sam to oznacza w polu `nordvik_period_stock_sum_not_additive`).
- Dostępność netto nie jest klipowana, a MOQ porównywane jest do pojedynczej linii.
- Biblioteka `openpyxl` nie jest zainstalowana w środowisku.

## Wymagania Marty vs. dane

- Ocena „co można potwierdzić” wymaga reguły: dostępność netto ≥ MOQ, status `confirmed`, wyłącznie zmapowane SKU. Taka reguła może być powtarzalnym zapytaniem.
- Dostępność nie jest prognozą popytu. Dane nie zawierają sprzedaży ani popytu.
- Żadna ilość nie jest zatwierdzonym zamówieniem.
- Jeśli kody nie łączą danych, rekomendacja się zatrzymuje. Dla 88% SKU łączenie z Nordvik nie jest możliwe.
- Dodatkowe wyciągi: udział `at_risk` wg marki, destynacji i tygodnia; linie z `PromisedDate` późniejszą niż potrzebny tydzień (data potrzebna nie występuje w danych); liczniki braków i wartości niepoprawnych; lista niezmapowanych SKU do wysłania do partnera.

## Decyzje wymagane przed dalszą pracą

1. Czy ujemną dostępność netto klipować do 0, czy oznaczać jako problem?
2. Które SKU i które sklepy są „wybrane”? Obecnie tylko 120 SKU ma mapowanie.
3. Którą migawkę (`AsOfDate`) uznać za aktualną: najnowszą (2026-10-26), czy wszystkie?
4. Czy MOQ dotyczy linii, czy zamówienia?
5. Z jaką datą porównywać `PromisedDate`? Data potrzebna przez Nordvik nie występuje w danych.
6. Czy dane syntetyczne mają być traktowane jako próbne? Wynika to z pliku, ale wymaga potwierdzenia od partnera.
7. Czy dla niezmapowanych SKU zamknąć rekomendację jako „nie można połączyć”, zgodnie z prośbą Marty?
