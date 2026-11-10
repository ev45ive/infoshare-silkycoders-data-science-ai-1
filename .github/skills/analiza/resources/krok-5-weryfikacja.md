# Krok 5: Weryfikacja wyniku

Cel: sprawdzić, czy wynik jest poprawny i stabilny, zanim trafi do odbiorcy.

## Propozycje kroków (do wyboru w todo i `vscode_askQuestions`)

- [ ] Drugie policzenie innym sposobem (inne zapytanie, inne źródło lub ręczny przykład)
- [ ] Porównanie z wartościami referencyjnymi (raport, poprzednia analiza)
- [ ] Test wrażliwości: inny okres, inny filtr, inna obsługa outlierów
- [ ] Sprawdzenie fanout przy JOIN-ach (liczba wierszy przed i po)
- [ ] Sprawdzenie mieszania okresów (pełny vs niepełny miesiąc)
- [ ] Rząd wielkości: czy liczby mają sens biznesowo
- [ ] Sprawdzenie, czy wniosek nie wynika z jednego segmentu

## Tryb wykonania (`vscode_askQuestions`)

- Agent uruchamia kod
- Agent zmienia pliki
- Użytkownik wykonuje ręcznie i zgłasza wynik

## Zasady

- Rozbieżność z wartością referencyjną nie jest błędem do ukrycia. Wyjaśnij ją lub zgłoś użytkownikowi.
- Wniosek, który nie przechodzi testu wrażliwości, oznacz jako warunkowy.

## Zapis w notebooku

Komórka markdown „Weryfikacja” z tabelą: kontrola, wynik, status. Komórki python z testami.

## Akceptacja

Zapytaj: „Czy wynik przeszedł weryfikację i można go oddać?” Tak: zapisz i przejdź do menu. Nie: wróć do propozycji kroków.
