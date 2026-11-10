# BC-04 — Sell-through i decyzja o wcześniejszej przecenie: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Prognoza, czy model sezonowy kolekcji AW26 osiągnie zdrowy sell-through do końca okresu pełnej ceny (8 tygodni od premiery), oraz decyzja, którym modelom pomóc wcześniej (przesunięcie zapasu, ekspozycja, wcześniejsza przecena).
- Dane: 4 kolekcje (SS25, AW25, SS26 zakończone; AW26 w toku), 96 modeli sezonowych (po 24 na kolekcję), sprzedaż i stany migawkowe.
- Kluczowe wyzwania: definicja etykiety (przeceny zanieczyszczają sell-through na koniec sezonu), mała liczba modeli, walidacja po kolekcjach, kalibracja, koszt decyzji.
- Punkt odcięcia: 2026-09-20.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| „Które modele AW26 nie osiągną zdrowego sell-through do końca okresu pełnej ceny?" | Etykieta: sell-through w 8. tygodniu od premiery przy pełnej cenie ≥ próg (roboczo 60%) |
| Decyzja podejmowana „na czuja" | Model ryzyka z kalibracją + reguła decyzyjna oparta na oczekiwanym koszcie |
| Przecena za wcześnie zabiera marżę, za późno zamraża zapas | Model kosztowy z jawnymi założeniami i analizą wrażliwości |
| Poziom decyzji: model (cała sieć); przesunięcia na poziomie sklepów | Jednostka analizy: `StyleCode` (cała sieć) × moment decyzji (tydzień 2–6 od premiery) |
| Transze AW26 (3, 17, 31 sierpnia) | Różny wiek modeli przy punkcie odcięcia: oceniać w aktualnym wieku każdego |
| Historia stanów | Eksport historyczny dla 3 zakończonych kolekcji o nieznanej jakości: audyt przed użyciem |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Kierownik merchandisingu z działem cen: ok. 7 tygodni po starcie AW26; decyzja o rabacie dziś „na czuja"; pytanie, które modele nie osiągną „zdrowego" sell-through do końca pełnej ceny (ok. 8 tygodni) i którym pomóc wcześniej; „zdrowy" roboczo 60% w 8. tygodniu; koszty nie policzone; termin: piątek.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online (online ma własny stan magazynowy); PLN; VAT 23%.
- Sezony: SS (luty–lipiec), AW (sierpień–styczeń). Cykl ceny: pełna cena, po ok. 8 tygodniach od premiery rabat −20…−30% (2–3 tygodnie), potem wyprzedaż −40…−60%. Rabat ustala dział cen per model.
- Rozmiary: popyt skupia się na M i L; XS i XL to ryzyko nadmiaru.
- Brak w danych: dostaw i przesunięć (jest tylko stan wynikowy), historii cennika, ID klienta, ruchu, pogody.

**Tabele** (`datasets/synthetic/bc04/`):
- `dim_date`, `dim_store`, `dim_product` (jak standardowo).
- `merch_plan`: `StyleCode`, `Collection` (`SS25`, `AW25`, `SS26`, `AW26`), `LaunchDate` (planowana), `PlannedUnits` (plan zakupu, cała sieć).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_inventory_daily`: `InventoryKey`, `DateKey`, `ProductKey`, `StoreKey`, `StockQuantity`, `LoadId` (migawka na koniec dnia).

**Ograniczenia dokumentowane.**
- Wyłącznie modele sezonowe 4 kolekcji; modele całoroczne poza zakresem.
- Odstępstwo od standardowej hurtowni: jednorazowy eksport historyczny stanów dla trzech zakończonych kolekcji (jakość nieznana).
- Stan to migawka; różnica migawek nie jest sprzedażą; wzrost stanu może oznaczać dostawę lub przesunięcie.
- `PlannedUnits` to plan, nie dostawa; `LaunchDate` planowana.
- Brak historii cennika; rabaty tylko w `DiscountAmount`.

**Definicje.** Sztuki; sprzedaż netto; stan magazynowy; sell-through = sprzedane / (sprzedane + stan na koniec okresu), liczony w obrębie sezonu (w zadaniu narastająco od premiery, sumowany po SKU i lokalizacjach modelu); dostępność; wartość zapasu w koszcie (koszt bieżący); tydzień ISO.

**Produkty końcowe.** Notebook, raport 1 strona (lista modeli AW26 z ryzykiem i rekomendacją, reguła decyzyjna), kod pomocniczy.

