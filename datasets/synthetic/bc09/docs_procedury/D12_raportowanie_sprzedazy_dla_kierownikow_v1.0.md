# Raportowanie sprzedaży dla kierowników sklepów

- **Wersja:** 1.0
- **Obowiązuje od:** 2025-04-15
- **Właściciel:** Controlling

## Cel
Dokument wskazuje kierownikom sklepów, w których raportach hurtowni danych sprawdzać podstawowe wskaźniki swojego sklepu.

## Sprzedaż dzienna
Sprzedaż dzienną sprawdzasz w widoku `reporting.vw_SalesDaily`, kolumna `Revenue`. Widok zawiera również sztuki, liczbę transakcji, rabaty i koszt własny w podziale na dni i sklepy.

## Sprzedaż tygodniowa
Sprzedaż tygodniową w podziale na kanał, region i kategorię sprawdzasz w widoku `reporting.vw_SalesWeekly`. Tygodnie liczone są według ISO-8601, od poniedziałku do niedzieli.

## Dostępność towaru
Dostępność towaru w sklepie sprawdzasz w widoku `reporting.vw_StockAvailability`. Dane o stanach magazynowych obejmują bieżący sezon.

## Zestawienie miesięczne
Miesięczne wyniki sklepu, w tym sprzedaż netto, koszt własny, zwroty i przychód na metr kwadratowy, znajdziesz w widoku `reporting.vw_StoreScorecard`.

## Terminy
Dane za dany dzień są dostępne w widokach następnego dnia roboczego. Zestawienie miesięczne jest zamykane po rozliczeniu zwrotów, zwykle do piątego dnia roboczego kolejnego miesiąca.

## Zasady korzystania
Wyniki widoków są przeznaczone do użytku wewnętrznego. Nie przekazuj ich osobom spoza sieci. Wątpliwości dotyczące interpretacji kolumn zgłaszaj do Controllingu.

## Odświeżanie danych
Widoki są odświeżane automatycznie w nocy. Jeśli dane za poprzedni dzień nie są widoczne rano, kierownik zgłasza to Controllingowi i nie próbuje ręcznie odtwarzać wartości z paragonów. Zapytania własne do hurtowni mogą uruchamiać wyłącznie osoby z odpowiednimi uprawnieniami.

## Kontakt
Pytania do właściciela dokumentu kieruj do Controllingu.
