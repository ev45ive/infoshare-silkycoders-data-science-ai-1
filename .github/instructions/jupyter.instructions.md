---
description: "Use when creating, editing, reviewing, or running Jupyter notebooks (.ipynb) for data analysis, EDA, charts, statistical tests, or business conclusions in Nordvik. Covers notebook section order, metadata cell, credentials, metric definitions, chart and test documentation, and conclusions."
applyTo: "**/*.ipynb"
---
# Zasady dla notebooków Jupyter

## Struktura
Zachowuj sekcje w tej kolejności (wzór w [jupyter-dokumentacja-i-przykłady.md](../../docs/jupyter-dokumentacja-i-przykłady.md)):
1. Metadata & Purpose (komórka markdown: autor, data, zespół, cel, hipotezy, wyniki)
2. Setup
3. Load Data
4. Explore
5. Transform
6. Analyze
7. Results & Conclusions
8. Appendix

## Dane
- Hasła i connection stringi czytaj wyłącznie ze zmiennych środowiskowych (`os.getenv`). Nigdy nie wpisuj ich w kod.
- Nie używaj danych symulowanych (np. `np.random`) jako wyników analizy. Przykładowy notebook w dokumentacji zawiera dane symulowane, nie kopiuj tego wzorca. Brak danych: zapytaj użytkownika.
- Zapytania SQL trzymaj w komórce albo w pliku `.sql` zgodnie z [sql.instructions.md](sql.instructions.md).
- Po wczytaniu danych wypisz wymiary (`print(f"Loaded {len(df)} rows")`) i pokaż `df.head()`.

## Metryki
- Przed policzeniem metryki sprawdź definicję w [slownik-metryk.md](../../docs/slownik-metryk.md) i podaj źródło w komórce markdown lub komentarzu.

## Kod
- Notebook musi przechodzić od góry do dołu bez błędów (Restart & Run All).
- Nie zostawiaj zakomentowanego kodu ani zmiennych z poprzednich uruchomień.
- Dla outputu dłuższego niż 10 wierszy użyj `.head()`, `.tail()` lub podsumowania.

## Wykresy i testy
- Każdy wykres: tytuł, podpisy osi z jednostką (np. PLN), legenda, gdy są serie.
- Test statystyczny: podaj metodę, poziom istotności (α) i założenia.

## Wnioski
- Odnoś wnioski do hipotez: potwierdzona lub odrzucona, z liczbami.
- Podawaj konkretne liczby (np. "wzrost o 28%"), nie ogólniki.
- Rekomendacje muszą być wykonalne (konkretny krok, nie ogólnik).
- Oddzielaj fakty od interpretacji.

## Weryfikacja
- Przed oddaniem notebooka przejdź checklistę z sekcji „Checklist Jupyter” w [jupyter-dokumentacja-i-przykłady.md](../../docs/jupyter-dokumentacja-i-przykłady.md).
