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
| Status | enum | `confirmed`, `at_risk`; znaczenie biznesowe nie zdefiniowane w profilu |
| PartnerNote | tekst | |

## Progi jakości

- Brak progów w profilu. Zapytać użytkownika przed dalszą pracą.
