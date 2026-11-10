# Krok 1: Wejście

Cel: ustalić pytanie biznesowe, źródła i lokalizację notebooka. Bez tego nie przechodzimy dalej.

## Kontekst z rozmowy

Najpierw sprawdź, czy odpowiedzi są już w kontekście (wiadomości użytkownika, `AGENTS.md`, `.github/copilot-instructions.md`). Jeśli tak, potwierdź je jednym pytaniem zamiast pytać od nowa.

## Pytania (`vscode_askQuestions`)

1. Problem biznesowy: jaka decyzja zależy od wyniku?
   - Propozycje: sprzedaż per sklep, zwroty, marża, stany magazynowe, inny (wpisz).
2. Źródła danych: skąd dane?
   - Propozycje: `datasets/daily_store_sales.csv`, `datasets/weekly_sales_lines.csv`, baza RetailDW (schematy `dw`, `reporting`), inne (wpisz).
3. Zakres czasowy i granulacja: jaki okres i jaki poziom (dzień, tydzień, sklep, SKU)?
4. Metryka: która z definicji w `docs/slownik-metryk.md`?
5. Odbiorca wyniku: kto przeczyta i w jakiej formie?
6. Lokalizacja notebooka: propozycja `notebooks/<nazwa-analizy>.ipynb`, inna (wpisz).

Pytania 3 do 5 pomiń, jeśli użytkownik już je podał w wiadomości.

## Otwarte pytania

Jeśli użytkownik nie zna odpowiedzi, zapisz pytanie jako otwarte i zaznacz je w notebooku. Nie wypełniaj luki założeniem.

## Zapis w notebooku

Pierwsza komórka markdown (bez kodu) z sekcjami:
- Problem biznesowy
- Pytanie analityczne
- Źródła danych (ścieżka lub tabela, data ekstrakcji, właściciel, jeśli znany)
- Metryki i ich definicje (z podaniem źródła)
- Zakres
- Otwarte pytania
- Log decyzji (data, decyzja, kto zdecydował)

## Akceptacja

Zapytaj: „Czy opis wejścia jest poprawny?” Tak: zapisz komórkę i wróć do menu. Nie: popraw wskazane punkty.
