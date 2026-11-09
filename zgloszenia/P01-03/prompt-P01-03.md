Rola: Jesteś senior data engineerem / data scientistem pracującym w zespole danych Nordvik.

Cel: Przygotować plan zmian dla zgłoszenia P01-03 (Marta, Merchandising), określić wpływ i ryzyka, oraz przygotować listę pytań doprecyzowujących. Zgłoszenie obejmuje:
- dodanie tabeli z rekomendacjami na poziomie model × sklep × tydzień,
- wprowadzenie wersjonowania wyników,
- usunięcie starego sygnału ceny.

Instrukcje:
- Przeanalizuj materiały w zgloszenia/P01-03/materialy-stat.
- Zaproponuj strukturę tabeli rekomendacji (model × sklep × tydzień) i opisz jej klucz oraz kolumny.
- Porównaj opcje wersjonowania wyników (do ustalenia, przedstaw alternatywy z zaletami i wadami).
- Wskaż kandydatów na stary sygnał ceny i sprawdź, czy jest jeszcze używany (gdzie to zweryfikować: kod, zapytania, dashboardy, joby, raporty).
- Opisz ryzyka dla każdej zmiany (wpływ na rekomendacje, forecasting, raporty, zależności).
- Sformułuj listę pytań doprecyzowujących dla Marty i zespołu.

Zasady:
- Nie zmieniaj żadnych plików.
- Nie ładuj datasetów.
- Nie wykonuj kroków zmian, tylko analiza i plan.

Format: Dokument .md z sekcjami (plan, wpływ, ryzyka, opcje wersjonowania, kandydaci na usunięcie sygnału ceny, pytania otwarte). Kod SQL w blokach ```sql.

Kontekst: Rekomendacje, forecasting i sygnał ceny. Nordvik to sieć mody: 5 sklepów stacjonarnych + ONLINE, przychód 78% STORE / 22% ONLINE, zwroty 4% / 18%.

Zgłoszenie: P01-03
