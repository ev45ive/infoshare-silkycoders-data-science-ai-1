---
name: partner-import
description: 'Process recurring partner data imports (xlsx/csv exports) for Nordvik: validate schema, normalize, check data quality, map SKUs, and answer business queries such as confirmable deliveries, at_risk share, unmapped SKUs. Use when: partner import, partner export, partner shipments, partner availability, dostępność partnera, import partnera, nowa wersja importu, nowy partner, profil importu, zapytanie biznesowe o dostawy, potwierdzenie dosyłki, PartnerSKU.'
argument-hint: 'Ścieżka do pliku importu lub nazwa profilu, np. partner_shipments_v3'
---

# Partner Import

Skill do cyklicznych importów danych od partnerów. Logika jest wspólna, a konfiguracja (profile, przepisy zapytań, decyzje, mapowania) należy do projektu.

## Krok 0: Inicjalizacja (zawsze pierwszy przy pierwszym użyciu w rozmowie)

1. Szukaj konfiguracji w kontekście: sekcja „Konfiguracja importów partnerów” w `AGENTS.md` w katalogu głównym, a następnie `.github/copilot-instructions.md` i wiadomości użytkownika w tej rozmowie.
2. Jeśli ścieżka jest w kontekście i katalog istnieje, użyj jej bez pytania. Ścieżkę rozwiązuj względem katalogu głównego workspace, nie bieżącego katalogu.
3. Jeśli ścieżki nie ma w kontekście lub katalog nie istnieje, wykonaj inicjalizację:
   - Sprawdź środowisko: `python3 -c "import openpyxl"`.
   - Jeśli `openpyxl` brakuje, zapytaj o zgodę na `pip install openpyxl`. Bez zgody nie instaluj i nie zakładaj, że biblioteka jest dostępna.
4. Zadaj pytania przez `vscode_askQuestions`, z propozycjami, w jednym wywołaniu:
   - Ścieżka importów: `./imports/` (zalecana), `./data/imports/`, inna (wpisz).
   - Katalog nie istnieje: utworzyć go teraz? Tak / Nie (zatrzymaj).
   - Zapis do `AGENTS.md` w sekcji „Konfiguracja importów partnerów”: Tak / Nie (tylko ta rozmowa).
   - Instalacja `openpyxl` (tylko jeśli brakuje): Tak, `pip install openpyxl` / Nie, zatrzymaj import.
5. Jeśli sekcja w `AGENTS.md` już istnieje, nie dodawaj drugiej. Zmianę wartości pokaż użytkownikowi i zapisz po zgodzie.
6. Jeśli użytkownik nie zgodzi się na zapis do `AGENTS.md`, użyj podanej ścieżki tylko w tej rozmowie i nie edytuj żadnych plików konfiguracyjnych.
7. Utwórz katalog dopiero po zgodzie z pkt 4.

Format wpisu w `AGENTS.md` (po zgodzie):

```markdown
## Konfiguracja importów partnerów
- Ścieżka importów: `./imports/`
- Profile: `./imports/profiles/`
- Przepisy zapytań: `./imports/recipes/`
- Rejestr decyzji: `./imports/decisions/otwarte-decyzje.md`
```

Nie wpisuj danych ani kluczy dostępowych do `AGENTS.md`.

## Krok 1: Ustalenie profilu

1. Dopasuj plik wejściowy do profilu w `{ścieżka}/profiles/`, używając nazwy arkusza, nagłówka w danym wierszu i listy kolumn. Jeśli pasuje więcej niż jeden profil lub żaden w pełni, zapytaj użytkownika zamiast wybierać.
2. Jeśli profilu nie ma, nie zgaduj schematu. Zaproponuj szkic profilu na podstawie nagłówka i zapytaj o brakujące pola (klucz biznesowy, grain, znaczenie `Status`, format dat, `MOQ`).
3. Zapisz nowy profil dopiero po zatwierdzeniu przez użytkownika.
4. Jeśli profil istnieje, a nagłówek się zmienił, zatrzymaj import i zaproponuj nową wersję profilu (`_vN`). Nie zmieniaj profilu po cichu.

## Krok 2: Walidacja i normalizacja

1. Sprawdź metadane w wierszach nad nagłówkiem oraz nagłówek względem profilu.
2. Daty mogą być numerami seryjnymi Excela (`date = 1899-12-30 + n` dni) lub `datetime`. Obsłuż oba typy.
3. Normalizacja: `strip()` dla tekstów, typy liczbowe, unikalność klucza, walidacja enumów.
4. Surowych wartości nie nadpisuj. Wartości netto zapisuj jako dodatkowe kolumny.
5. Liczniki jakości (duplikaty, braki, wartości ujemne, wartości spoza enumów) zapisuj jako osobne zestawienie. Nie ukrywaj ich.
6. Porównaj liczniki z poprzednim importem, jeśli istnieje. Progi zatrzymania (np. maksymalna liczba braków) pochodzą z profilu. Jeśli progu brak, zapytaj użytkownika przed dalszą pracą.

## Krok 3: Mapowanie SKU

- Łącz wyłącznie przez `PartnerSKU` z pliku mapowania w `{ścieżka}/mappings/`.
0. Każdy szablon analizy zaczynaj od doprecyzowania wejść i zakresu przez `vscode_askQuestions` (z propozycjami). Pytaj o:
   - pliki i wersje profili,
   - pytanie biznesowe i metrykę,
   - zakres: marki, destynacje, tygodnie, SKU,
   - migawkę dostępności (np. najnowsza albo konkretna data),
   - poziom MOQ (linia czy zamówienie),
   - format wyniku.
   Bez odpowiedzi nie licz. Brakujące informacje zapytaj, nie zakładaj.
- Nie używaj nazwy marki ani identyfikatorów linii jako klucza łączenia.
- Wiersze bez mapowania trafiają do osobnego zestawienia „niezmapowane”.

## Krok 4: Zapytania biznesowe

1. Przed policzeniem metryki sprawdź jej definicję w [docs/slownik-metryk.md](../../../docs/slownik-metryk.md) i podaj źródło.
2. Jeśli istnieje przepis w `{ścieżka}/recipes/`, użyj go. Jeśli nie, opisz pytanie, wejścia i metrykę, a po zatwierdzeniu dodaj przepis.
3. Przed rekomendacją sprawdź rejestr decyzji `{ścieżka}/decisions/`. Jeśli wymagana decyzja jest otwarta, zatrzymaj rekomendację i wskaż, czego brakuje.
4. Wpisy w rejestrze decyzji tworzy i zamyka wyłącznie użytkownik. Agent może co najwyżej zaproponować treść wpisu.
5. Każdy wynik podaj jako: „możliwe do potwierdzenia” lub „zatrzymane”, z listą założeń, ograniczeń i etykietą „dane syntetyczne”, jeśli plik tak jest oznaczony. Nie nazywaj wyniku zamówieniem ani potwierdzoną dostawą.

## Zasady stałe

- Dostępność nie jest prognozą popytu. Ilość nie jest zatwierdzonym zamówieniem.
- `at_risk` nie oznacza anulowania.
- `AvailableUnits` to stan migawki i nie sumuje się po tygodniach. `UnitsBooked` to przepływ i sumuje się.
- Nie czytaj plików z `zgloszenia/`, `notatki/` ani `.specstory/`, chyba że użytkownik poda plik bezpośrednio.
- Nie czytaj dużych plików danych do kontekstu. Używaj skryptów Python do schematu i agregacji.
- Nie zapisuj poza katalogiem importów i `AGENTS.md`, a do `AGENTS.md` tylko po zgodzie.
- Przed zapisem profilu, przepisu lub `AGENTS.md` pokaż zmianę i poczekaj na zgodę.
- Nie instaluj pakietów bez zgody użytkownika.
- Nie przyjmuj własnych założeń o danych, np. klipowania ujemnej dostępności do 0 czy znaczenia MOQ. Zapytaj.
- Nie zgaduj. Brakujące informacje zapytaj użytkownika.
