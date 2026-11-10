# Profil: partner_shipments_v3

- Plik testowy: zgloszenia/P01-04/partner_shipments_v3.xlsx
- Arkusz: `Partner export`
- Wiersze metadanych: 1–2 (pomijane)
- Nagłówek: wiersz 3
- Dane: od wiersza 4
- Klucz biznesowy: `PartnerLineId` (unikalny)
- Grain: jedna linia partnera

## Kolumny

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| PartnerLineId | tekst | klucz |
| PartnerBrand | tekst | |
| PartnerSKU | tekst | klucz mapowania (Krok 3) |
| Destination | tekst | |
| WeekStart | data | Excel serial lub datetime |
| UnitsBooked | liczba | przepływ, sumuje się |
| PromisedDate | data | Excel serial lub datetime |
| Status | enum | `confirmed`, `at_risk`; etykiety partnera bez własnej interpretacji. `at_risk` nie oznacza anulowania, `confirmed` nie jest gwarancją dostawy (decyzja P1) |
| PartnerNote | tekst | |

## Progi jakości

- Bez progów. Zatrzymanie importu tylko przy błędach schematu (brak nagłówka lub kolumny).
