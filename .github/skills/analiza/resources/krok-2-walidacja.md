# Krok 2: Walidacja danych

Cel: sprawdzić, czy dane nadają się do analizy, zanim cokolwiek policzymy.

## Propozycje kroków (do wyboru w todo i `vscode_askQuestions`)

- [ ] Schemat: nazwy kolumn, typy, format dat
- [ ] Liczba wierszy i zakres dat
- [ ] Granulacja: czy wiersz = to, co zakłada pytanie
- [ ] Duplikaty kluczy (naturalnych i surogatowych)
- [ ] Braki (NULL) per kolumna z udziałem procentowym
- [ ] Wartości spoza dziedziny: ujemne ilości, ceny 0, daty z przyszłości
- [ ] Wartości kategoryczne: nowe kody, literówki, różne zapisy tego samego
- [ ] Kompletność szeregu: brakujące dni, sklepy, kategorie
- [ ] Spójność sum: źródło vs po transformacji
- [ ] Zgodność z definicją metryki z `docs/slownik-metryk.md`
- [ ] Porównanie z poprzednim ekstraktem, jeśli istnieje

## Tryb wykonania (`vscode_askQuestions`)

- Agent uruchamia kod (Python lub SQL, tylko na danych agregowanych lub schemacie)
- Agent zmienia pliki (np. dodaje skrypt walidacyjny)
- Użytkownik wykonuje ręcznie i zgłasza wynik

## Wynik do pokazania

Tabela z kontrolami: nazwa kontroli, wynik, próg (jeśli jest), status (OK, uwaga, blokada). Progi brakujące w dokumentacji pytaj, nie zakładaj.

## Zasady

- Liczniki jakości zapisuj jako osobne zestawienie. Nie usuwaj i nie nadpisuj surowych danych.
- Blokada (np. duplikaty kluczy) zatrzymuje analizę do decyzji użytkownika.

## Zapis w notebooku

Komórka markdown „Walidacja” z tabelą kontroli i decyzjami o wykluczeniach, oraz komórka python z kodem kontroli.

## Akceptacja

Zapytaj: „Czy walidacja jest zaakceptowana? Czy można przejść dalej?” Tak: zapisz i przejdź do menu. Nie: wróć do propozycji kroków tego samego kroku.
