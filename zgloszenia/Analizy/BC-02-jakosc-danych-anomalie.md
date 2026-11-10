# BC-02 — Jakość ładowania danych i wykrywanie anomalii: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Wykrywanie problemów z danymi sprzedaży w procesie ładowania hurtowni: duplikaty plików, brakujące dane sklepów, błędne ceny i ilości, ciche odrzucenia wierszy, nieudane uruchomienia.
- Porównanie trzech warstw detekcji: reguły deterministyczne, statystyka wolumenu, model wielocechowy (Isolation Forest). Miara: przyrost każdej warstwy ponad poprzednie.
- Ocena bez etykiet: własny generator wstrzykniętych anomalii, adiudykacja flag w historii, budżet fałszywych alarmów.
- Okres danych: 2025-01-01 do 2026-09-20 (ładowania do 2026-09-21).

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| Raport pokazał podwójną sprzedaż, brak sklepu, dziwne ceny; zauważano po 1–2 dniach | Taksonomia problemów i detekcja przed przeliczeniem raportu |
| „Czy da się prostymi regułami, czy potrzebny model?" | Porównanie M0 reguły, M1 progi wolumenu, M2 reszty z modelu sezonowego, M3 Isolation Forest |
| Koszt alarmu 20 minut, budżet ≤ 2 fałszywe alarmy miesięcznie dla sieci | Raportowanie fałszywych alarmów na miesiąc i precyzji przy realnej częstości (ok. 1 problem miesięcznie) |
| „Wstrzymać przeliczenie czy tylko ostrzec?" | Poziomy alarmu (blokada, ostrzeżenie, informacja) i runbook per typ |
| Brak etykiet historycznych | Wstrzykiwanie własnych anomalii (recall z przedziałem), adiudykacja flag, klucz na końcu |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Kierownik Data Engineeringu z controllingiem: w ostatnich miesiącach raport pokazał dwukrotną sprzedaż jednego dnia, brak jednego sklepu, dziwne ceny; zauważano po dniu lub dwóch; potrzebne automatyczne wykrywanie, najlepiej przed przeliczeniem hurtowni; pytania: jakie rodzaje problemów występują, co reguły a co model, ile fałszywych alarmów (20 minut, ≤ 2/mies.), co robić po alarmie.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów (`S-WAW-01`, `S-WAW-02`, `S-KRK-01`, `S-POZ-01`, `S-GDA-01`) i online (`S-ONL-01`); PLN; VAT 23%.
- Katalog 14 modeli (ok. 120 SKU). Jedna cena katalogowa modelu; rabaty tylko w `DiscountAmount`.
- Szczyty: Black Friday, grudzień; luty najsłabszy. Pliki źródłowe raz na dobę.
- Stacjonarne zamknięte w święta i większość niedziel (z wyjątkiem niedziel handlowych); online codziennie.

**Tabele** (`datasets/synthetic/bc02/`):
- `dim_date`, `dim_store`, `dim_product` (kolumny jak w standardowej hurtowni).
- `src_sales_raw`: `RawId`, `TransactionNo`, `LineNumber`, `SalesDate`, `SKU`, `StoreCode`, `Quantity`, `UnitPrice`, `DiscountAmount` (wszystko tekst), `SourceFile`, `ExtractedAt`.
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `load_log`: `LoadId`, `PackageName`, `StartedAt`, `FinishedAt`, `Status` (`SUCCEEDED`/`FAILED`), `RowsRead`, `RowsLoaded`, `RowsRejected`, `ErrorMessage`.

**Opis ładowania.**
- Pliki `POS_yyyymmdd.csv` (wszystkie sklepy stacjonarne) i `WEB_yyyymmdd.csv` trafiają do `src_sales_raw` bez walidacji (`SourceFile`).
- Krok 1: konwersja typów; wiersz z pustym lub niekonwertowalnym `TransactionNo`, `LineNumber`, `SalesDate`, `SKU`, `StoreCode`, `Quantity`, `UnitPrice` jest po cichu odrzucany; niekonwertowalny `DiscountAmount` → 0.
- Krok 2: złączenie z wymiarami (data, SKU, kod sklepu); brak dopasowania odrzuca wiersz.
- Pełne przeładowanie przy każdym uruchomieniu: `load_log` ma jeden wiersz dziennie; `RowsRead` = liczba wierszy w `src_sales_raw` narastająco, `RowsLoaded` = wiersze w `fact_sales`, `RowsRejected` = różnica; `FAILED` zostawia poprzedni stan faktów.
- Brak deduplikacji i brak walidacji cen i ilości.
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Sztuki; sprzedaż netto; liczba transakcji = `COUNT(DISTINCT TransactionNo)`; UPT; stopa rabatu; średnia cena netto sztuki; wiersze odrzucone = `RowsRead − RowsLoaded`.

**Produkty końcowe.** Notebook, raport 1 strona z macierzą detekcji i runbookiem, kod pomocniczy i SQL z nagłówkiem.
