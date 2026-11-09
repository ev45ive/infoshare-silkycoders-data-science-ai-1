# Rejestr decyzji: import partnerów

Wpisy tworzy i zamyka wyłącznie użytkownik.

| Nr | Temat | Propozycja | Wada / uwaga | Status |
| --- | --- | --- | --- | --- |
| P1 | Znaczenie `Status` | Traktować `confirmed` i `at_risk` jako etykiety partnera, bez własnej interpretacji. `at_risk` nie oznacza anulowania. | Nie wiadomo, czy `confirmed` oznacza gwarantowaną dostawę. | zaakceptowana (użytkownik, 2026-11-09) |
| P2 | Poziom MOQ | W pierwszym przebiegu liczyć na poziomie linii i oznaczyć to w wyniku. Poziom zamówienia dopiero po zdefiniowaniu zamówienia. | Wybrany wcześniej poziom zamówienia wymaga definicji zamówienia, której nie ma. Wrażliwość 1 938 nie obowiązuje przy poziomie zamówienia. | zaakceptowana (użytkownik, 2026-11-09) |
| P3 | Migawka dostępności | Najnowsza migawka (2026-10-26), opisana jako stan na dzień. | Dostępność nie sumuje się po tygodniach. | zaakceptowana (użytkownik, 2026-11-09) |
| P4 | Zakres | Wszystkie marki, destynacje i 4 tygodnie. Wynik pokazuje 880 niezmapowanych SKU. | Tylko 120 z 1 000 SKU ma mapowanie. | zaakceptowana (użytkownik, 2026-11-09) |
| P5 | Pytanie Marty | „Ile linii ze statusem `confirmed` ma dostępność netto ≥ MOQ na migawce 2026-10-26” (MOQ na poziomie linii). | Nie nazywamy wyniku potwierdzoną dostawą. | zaakceptowana (użytkownik, 2026-11-09) |
| P6 | Klipowanie ujemnej dostępności netto | Nie klipować, pokazać wartości ujemne osobno jako sygnał. | W teście klipowanie nie zmieniło wyniku. Decyzja techniczna. | zaakceptowana (użytkownik, 2026-11-09) |