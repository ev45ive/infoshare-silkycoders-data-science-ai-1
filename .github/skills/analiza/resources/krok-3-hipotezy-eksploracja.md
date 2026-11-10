# Krok 3: Hipotezy i eksploracja danych

Cel: sformułować hipotezy przed analizą i zebrać obserwacje, które je wspierają lub obalają.

## Hipotezy

Zaproponuj 2 do 4 hipotez w formie: „Zmienna X wpływa na Y w segmencie Z, bo…”. Dla każdej podaj:
- kryterium potwierdzenia (np. różnica większa niż próg biznesowy),
- kryterium odrzucenia,
- dane potrzebne do sprawdzenia.

Hipotezy zatwierdza użytkownik przez `vscode_askQuestions` przed eksploracją.

## Propozycje kroków (do wyboru w todo i `vscode_askQuestions`)

- [ ] Rozkłady zmiennych (histogram, boxplot) i wartości odstające
- [ ] Szereg czasowy: trend, sezonowość, efekty kalendarzowe
- [ ] Podział na segmenty: sklep, kategoria, kanał (online vs stacjonarny)
- [ ] Zależności między zmiennymi (korelacja, tabela krzyżowa)
- [ ] Sprawdzenie, czy wynik nie zależy od jednego sklepu, produktu lub okresu
- [ ] Lista zaskoczeń i pytań do użytkownika

## Tryb wykonania (`vscode_askQuestions`)

- Agent uruchamia kod
- Agent zmienia pliki
- Użytkownik wykonuje ręcznie i zgłasza wynik

## Zasady

- Hipotez nie zmieniaj po zobaczeniu wyniku. Jeśli zmieniasz, oznacz to jako eksplorację, nie potwierdzenie.
- Obserwacje zapisuj z liczbami, nie tylko z opisem wykresu.

## Zapis w notebooku

Komórka markdown „Hipotezy” (lista z kryteriami), komórki python z eksploracją, komórka markdown „Obserwacje” z listą wniosków i zaskoczeń.

## Akceptacja

Zapytaj: „Czy obserwacje są zaakceptowane i które hipotezy przechodzą do analizy?” Tak: zapisz i przejdź do menu. Nie: wróć do propozycji.
