# Krok 6: Reprodukowalność

Cel: zapewnić, że analizę da się powtórzyć przez inną osobę lub w przyszłości.

## Propozycje kroków (do wyboru w todo i `vscode_askQuestions`)

- [ ] Notebook uruchamia się od początku do końca (Restart & Run All)
- [ ] Ustalone ziarno losowości (jeśli są losowe elementy)
- [ ] Wersje bibliotek zapisane (np. w pierwszej komórce lub w `requirements`)
- [ ] Data ekstrakcji danych i ścieżka lub zapytanie źródłowe zapisane
- [ ] Zapytania SQL z nagłówkiem (cel, źródła, założenia)
- [ ] Ścieżki względne, bez lokalnych ścieżek użytkownika
- [ ] Brak danych wrażliwych ani kluczy dostępowych w notebooku

## Tryb wykonania (`vscode_askQuestions`)

- Agent uruchamia kod (np. Restart & Run All, jeśli środowisko to umożliwia)
- Agent zmienia pliki
- Użytkownik wykonuje ręcznie i zgłasza wynik

## Zapis w notebooku

Komórka markdown „Reprodukowalność” z listą spełnionych punktów i ograniczeń.

## Akceptacja

Zapytaj: „Czy reprodukowalność jest zaakceptowana?” Tak: zapisz i przejdź do menu. Nie: popraw wskazane punkty.
