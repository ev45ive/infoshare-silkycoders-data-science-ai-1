---
name: analiza
description: 'Prowadzi analizę danych krok po kroku dla Nordvik: wejście (problem biznesowy, źródła, lokalizacja notebooka), walidacja danych, hipotezy i eksploracja, analiza, weryfikacja, reprodukowalność, podsumowanie. Każdy krok ładowany na żądanie z osobnego zasobu. Use when: analiza, nowa analiza, zacznij analizę, walidacja danych, eksploracja danych, hipotezy, weryfikacja wyniku, reprodukowalność, podsumowanie analizy, notebook analityczny.'
argument-hint: 'Nazwa analizy lub numer kroku, np. krok 2'
disable-model-invocation: true
user-invocable: true
---

# Analiza

Skill prowadzi analizę danych w pętlach. Użytkownik wybiera krok, agent go wykonuje, a po akceptacji zapisuje wynik do notebooka i dopiero wtedy przechodzi dalej.

## Zasady stałe

- Nie zgaduj. Brakujące informacje pytaj przez `vscode_askQuestions`, z propozycjami do wyboru.
- Nie szukaj plików samodzielnie bez zgody użytkownika. Najpierw zapytaj o źródło.
- Nie czytaj plików z `zgloszenia/`, `notatki/`, `.specstory/` ani `docs/ai-sessions/`, chyba że użytkownik przekaże plik bezpośrednio.
- Nie czytaj dużych plików danych (`datasets/`, `.csv`, `.xlsx`) do kontekstu. Używaj Pythona lub SQL do schematu i agregacji.
- Definicje metryk sprawdzaj w [docs/slownik-metryk.md](../../../docs/slownik-metryk.md) przed każdym policzeniem i podawaj źródło.
- Nie przechodź do kolejnego kroku bez akceptacji użytkownika.
- W wiadomościach do użytkownika odwołuj się do komórek numerem (od 1), nie identyfikatorem.

## Proces pętli

Każdy krok (poza podsumowaniem) przebiega tak samo:

1. Załaduj zasób kroku z tabeli poniżej (tylko wybrany krok).
2. Zaproponuj listę działań jako todo (`manage_todo_list`) i zapytaj w `vscode_askQuestions`, które wykonać.
3. Zapytaj o tryb wykonania: agent uruchamia kod, agent wprowadza zmiany w plikach, albo użytkownik wykonuje ręcznie i zgłasza wynik.
4. Wykonaj wybrane działania. Oznaczaj todo jako wykonane od razu po zakończeniu każdego z nich.
5. Pokaż wynik w skrócie (liczby, wnioski, otwarte problemy).
6. Zapytaj o akceptację:
   - Tak: zapisz wynik do notebooka jako komórki markdown i python, potem przejdź do menu kroków.
   - Nie: zapytaj, co poprawić, i wróć do punktu 2 tego samego kroku.
7. Otwarte pytania zapisuj w notebooku w sekcji „Otwarte pytania”, jeśli nie zostały rozstrzygnięte.

## Kroki i zasoby

| Krok | Zasób (ładuj na żądanie) |
| --- | --- |
| 1. Wejście: problem, źródła, lokalizacja notebooka | [resources/krok-1-wejscie.md](resources/krok-1-wejscie.md) |
| 2. Walidacja danych | [resources/krok-2-walidacja.md](resources/krok-2-walidacja.md) |
| 3. Hipotezy i eksploracja | [resources/krok-3-hipotezy-eksploracja.md](resources/krok-3-hipotezy-eksploracja.md) |
| 4. Analiza i testy | [resources/krok-4-analiza.md](resources/krok-4-analiza.md) |
| 5. Weryfikacja wyniku | [resources/krok-5-weryfikacja.md](resources/krok-5-weryfikacja.md) |
| 6. Reprodukowalność | [resources/krok-6-reprodukowalnosc.md](resources/krok-6-reprodukowalnosc.md) |
| Podsumowanie wyników | [resources/podsumowanie-szablon.md](resources/podsumowanie-szablon.md) oraz [resources/podsumowanie-checklista.md](resources/podsumowanie-checklista.md) |

## Menu na początku

Przy każdym wywołaniu pokaż użytkownikowi, które kroki są zrobione (na podstawie notebooka), i zapytaj, który wykonać w `vscode_askQuestions`. Użytkownik może wybrać kilka kroków, ale każdy wykonujemy osobno, w kolejności.

## Zakończenie analizy

Po zaakceptowaniu kroków 1 do 6 załaduj zasób podsumowania, wypełnij szablon w notebooku, przejdź przez checklistę i zapytaj o ostateczną akceptację.
