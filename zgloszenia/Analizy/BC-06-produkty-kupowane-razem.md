# BC-06 — Produkty kupowane razem: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Współwystępowanie modeli w paragonach (`TransactionNo`): które pary warto eksponować razem w sklepach i online, zaczynając od kurtek.
- Porównanie: ranking popularności (baseline), statystyki par z kontrolą sezonu, reguły asocjacyjne (FP-Growth), podobieństwo przedmiotów (SVD, cosinus).
- Kluczowe zagadnienia: definicja koszyka i jednostki, sezonowość zawyżająca lift, minimalne wsparcie i FDR, walidacja w czasie, różnice kanałów, lift ≠ efekt przyczynowy.
- Okres: 2025-01-01 do 2026-09-20; katalog 36 modeli; brak ID klienta.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| Moduł „uzupełnij stylizację" i ekspozycja w sklepach | Ranking top-k uzupełnień per model kotwica i kanał |
| „Co kupuje się razem z kurtką?" | Pary i ufność P(B \| A) dla modeli kurtek, lift po kontroli sezonu |
| Brak ID klienta, tylko paragony | „Razem" = ten sam paragon; nie wiadomo, czy osobne wizyty |
| Dwa kanały o odmiennym zachowaniu | Analiza osobno dla sklepów i online |
| Wartość biznesowa | Górna granica przyrostu (koszyki × różnica P(B\|A) − P(B) × cena B), nie prognoza; propozycja testu A/B |
| Jakość rekomendacji | Trafienie w top-k przy ukryciu jednego elementu paragonu (hit-rate@k, MRR), porównanie z popularnością |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** E-commerce z merchandisingiem: moduł „uzupełnij stylizację" i ekspozycja w sklepach; start od kurtek; pytanie, co najczęściej kupuje się razem z kurtką i które pary eksponować w sklepach i online; brak identyfikatora klienta, tylko paragony.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online; PLN; VAT 23%. Kategorie: Kurtki, Sukienki, Swetry, Jeansy, T-shirty, Koszule, Akcesoria.
- Sprzedaż większości kategorii jest sezonowa (kurtki, swetry, szaliki zimą; sukienki, T-shirty latem). UPT typowo 2–4.
- Brak w danych: ID klienta, karty lojalnościowej, ruchu na stronie, dostaw, historii cennika, pogody.

**Tabele** (`datasets/synthetic/bc06/`):
- `dim_date`, `dim_store`, `dim_product` (36 modeli).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.

**Ograniczenia dokumentowane.**
- Paragon = `TransactionNo`; `COUNT(*)` to liczba pozycji, nie transakcji.
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Liczba transakcji = `COUNT(DISTINCT TransactionNo)`; UPT; sztuki; sprzedaż netto; tydzień ISO; miary współwystępowania do własnej definicji: wsparcie (udział koszyków zawierających zestaw), ufność P(B|A), lift = P(A i B) / (P(A) × P(B)); populacja bazowa (wszystkie koszyki czy wieloproduktowe) do uzasadnienia.

**Produkty końcowe.** Notebook, raport 1 strona (rekomendowane pary z pewnością, osobno sklepy i online, górna granica wartości, propozycja testu A/B), kod pomocniczy.

