# Profil: partner_availability_v2

- Plik testowy: zgloszenia/P01-04/partner_availability_v2.xlsx
- Arkusz: `Partner export`
- Wiersze metadanych: 1–2 (pomijane)
- Nagłówek: wiersz 3
- Dane: od wiersza 4
- Klucz biznesowy: `SnapshotId` (unikalny)
- Grain: jedna migawka dostępności na linię partnera

## Kolumny

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| SnapshotId | tekst | klucz |
| PartnerBrand | tekst | |
| PartnerSKU | tekst | klucz mapowania (Krok 3) |
| Destination | tekst | |
| AsOfDate | data | Excel serial lub datetime; migawka, nie sumuje się po tygodniach |
| AvailableUnits | liczba | stan migawki |
| ReservedUnits | liczba | stan migawki |
| MOQ | liczba | poziom linii, na linię PartnerSKU + Destination (decyzja P2) |
| AvailabilityNote | tekst | |

## Zasady

- Wynik na migawce najnowszej: `AsOfDate` = 2026-10-26 (decyzja P3).
- Dostępność netto = `AvailableUnits` − `ReservedUnits`, bez klipowania do 0; wartości ujemne pokazywać osobno jako sygnał (decyzja P6).

## Progi jakości

- Bez progów. Zatrzymanie importu tylko przy błędach schematu (brak nagłówka lub kolumny).
