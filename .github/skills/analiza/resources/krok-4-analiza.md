# Krok 4: Analiza i testy

Cel: odpowiedzieć na pytanie analityczne metodą dobraną do danych i hipotez.

## Propozycje kroków (do wyboru w todo i `vscode_askQuestions`)

- [ ] Wybór metody: porównanie grup, szereg czasowy, regresja, test nieparametryczny
- [ ] Ustalenie progu istotności i minimalnego efektu istotnego biznesowo (zatwierdza użytkownik)
- [ ] Wielkość próby i moc testu; przy małej próbie zaznacz ograniczenie
- [ ] Korekta na wielokrotne porównania, jeśli testujemy wiele segmentów
- [ ] Kontrola zmiennych zakłócających (sezonowość, promocje, wielkość sklepu)
- [ ] Przedziały ufności obok wartości p
- [ ] Rozróżnienie korelacji od przyczynowości; przy eksperymencie sprawdź randomizację i balans grup

## Tryb wykonania (`vscode_askQuestions`)

- Agent uruchamia kod
- Agent zmienia pliki
- Użytkownik wykonuje ręcznie i zgłasza wynik

## Zasady

- Kryteria decyzji ustal przed uruchomieniem testu.
- Wynik podawaj jako: efekt, przedział ufności, wartość p (jeśli dotyczy), wielkość próby.
- Przy wnioskach przyczynowych bez eksperymentu oznacz to jako interpretację.

## Zapis w notebooku

Komórka markdown „Metoda i założenia”, komórki python z testami, komórka markdown „Wyniki” z tabelą i wnioskiem w języku biznesu.

## Akceptacja

Zapytaj: „Czy wyniki i wnioski są zaakceptowane?” Tak: zapisz i przejdź do menu. Nie: wróć do wyboru metody lub kroków.
