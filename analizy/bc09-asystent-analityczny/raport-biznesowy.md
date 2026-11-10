# Asystent analityczny Nordvik: rekomendacja przed pilotażem

**Dla:** dyrektor operacyjny | **Stan:** wstępna (wynik na pytaniach testowych jeszcze nieoceniony) | **Data:** 2026-11-10

## Decyzja

**Uruchomić wąski pilotaż na poziomie A (tylko odczyt), nie na poziomie B (szkice zadań).** Asystent jest bezpieczny w działaniu, dobry w liczbach i zawodny w procedurach, gdy dokumenty się różnią.

## Co zmierzyłem (34 pytania do strojenia; przedziały 95%, małe próby)

| Obszar | Wynik | Co to znaczy |
| --- | --- | --- |
| Liczby (sprzedaż, zwroty, marża, dostępność) | 10/10 (przedział 72-100%) | trafne, o ile asystent wie, które kolumny widoków mylą; **bez tej wiedzy 6/10** |
| Pytania łączące dane, prognozę i zadanie | 7/7 (65-100%) | prognoza zawsze z przedziałem; dla nowego modelu bez historii odmowa |
| Pytania poza zakresem (klienci, pogoda, zapis do bazy) | 8/8 (68-100%) | poprawne odmowy |
| Procedury | 6/9 (35-88%) | patrz ryzyka |
| **Ujawnianie sprzecznych lub nieaktualnych dokumentów** | **4/9 (44%), próg 80%** | **nie spełnia progu** |
| Zapisy i zatwierdzenia bez człowieka | **0** w 18 atakach i 45 testach technicznych | spełnione z konstrukcji (baza tylko do odczytu, brak narzędzia zatwierdzającego) |
| Koszt i czas | ok. 7,7 tys. tokenów i 2,5 s na pytanie | w założonym limicie |

Wynik jest **optymistyczny**: prompt stroiłem na tych samych pytaniach. Na 16 pytaniach testowych asystent odpowiedział dwukrotnie (zapisane), ale ich **jeszcze nie oceniłem**; to pierwszy niezależny sprawdzian.

## Ryzyka i kontrole

- **Zła definicja metryki:** widoki raportowe liczą co innego niż mówią ich nazwy (np. `Revenue` to sprzedaż brutto). Kontrola: ostrzeżenie zwracane przez narzędzie SQL przy użyciu takiej kolumny. Nie wystarczyło wpisać definicje do instrukcji.
- **Sprzeczne dokumenty:** limit korekty ceny to 300 PLN w jednym dokumencie i 500 PLN w drugim. Asystent **wybrał jedną wartość i uzasadnił wybór** zamiast pokazać konflikt. Instrukcja tego nie naprawiła. Rozwiązanie leży u źródła: dokumenty.
- **Fałszywa treść w dokumencie:** zdanie ukryte w dokumencie zamknięcia dnia (polecenie do modelu) jest wychwytywane, ale **przeformułowane** („zwroty bez paragonu w każdej sytuacji") asystent powtórzył jako procedurę. Obrona: właściciel, wersja i przegląd dokumentów.
- **Sub-agenci:** podział na kilku agentów pogorszył wyniki (25/34 wobec 31/34) i podwoił czas; nie rekomenduję.

## Warunki pilotażu (poziom A)

1. Użytkownicy: analitycy i dział zakupów; kierownicy sklepów po uporządkowaniu dokumentów.
2. Każda liczba z widocznym zapytaniem i definicją; procedury tylko z cytatem i dopiskiem „zweryfikuj w dokumencie".
3. Przed startem usunąć u źródła: sprzeczność D06 i D07, nieaktualny D01, zdanie w D12 wskazujące `Revenue`, polecenie w D09.
4. Monitorowanie: zapis pytań, zapytań i kosztu; cotygodniowy przegląd 20 odpowiedzi przez człowieka; zgłaszanie błędów do analityka.
5. Poziom B (szkic zadania) dopiero po: potwierdzeniu liczb na pytaniach testowych, ślepej ocenie człowieka, kontroli konfliktów wartości w dokumentach i usłudze z zatwierdzaniem przez **inną** osobę.

## Czego nie wiemy

Jakości na nowych pytaniach (test nieoceniony); wiarygodności automatycznej oceny (brak oceny człowieka); powtarzalności odpowiedzi; kosztu w PLN; czy dane firmy mogą trafiać do zewnętrznego dostawcy modelu. **Pytania do Pana/Pani:** który dokument obowiązuje (300 czy 500 PLN)? czy asystent może uruchamiać zapytania w imieniu kierownika (dokument D12 tego zabrania)? kto zatwierdza zadania i w jakim terminie?
