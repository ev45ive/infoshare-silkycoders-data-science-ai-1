# Eksperyment v1: linie `confirmed` z dostępnością netto ≥ MOQ

Data: 2026-11-09. Status eksperymentu: zaakceptowany przez użytkownika (2026-11-10). Status wyniku: możliwe do potwierdzenia (z założeniami poniżej).

## Pytanie

Ile linii ze statusem `confirmed` ma dostępność netto ≥ MOQ na migawce 2026-10-26? (P5, zaakceptowane w [rejestrze decyzji](../decisions/otwarte-decyzje.md))

## Wejścia

- `zgloszenia/P01-04/partner_shipments_v3.xlsx` (profil: `partner_shipments_v3`)
- `zgloszenia/P01-04/partner_availability_v2.xlsx` (profil: `partner_availability_v2`)
- `zgloszenia/P01-04/nordvik_assortment_map.csv` (mapowanie po `PartnerSKU`)

## Zakres

- Zmapowane linie: 120 SKU, 4 tygodnie, 6 destynacji.
- Niezmapowane SKU (880) są poza wynikiem (P4).

## Metoda

1. Linie przesyłek ze statusem `confirmed` i zmapowanym `PartnerSKU`.
2. Połączenie z migawką dostępności po `PartnerSKU` i `Destination`, wybór migawki z `AsOfDate` = 2026-10-26.
3. Dostępność netto = `AvailableUnits` − `ReservedUnits`. MOQ na poziomie linii (P2).
4. Dostępność netto nie jest obcinana do 0. Obcięcie nie zmienia wyniku (P6).

## Wynik

| Miara | Wartość |
| --- | --- |
| Zmapowane linie `confirmed` | 2 560 |
| Linie z dostępnością netto ≥ MOQ (migawka 2026-10-26) | 1 938 |
| Linie bez migawki dla pary SKU+Destination | 0 |

## Założenia i ograniczenia

- `confirmed` to etykieta partnera, nie gwarancja dostawy (P1).
- Wynik nie jest zamówieniem ani potwierdzoną dostawą.
- Migawka S0002007 nie ma MOQ, ale ma `AsOfDate` 2026-10-05, więc nie wpływa na wynik.
- Definicje metryk nie zostały sprawdzone w `docs/slownik-metryk.md` w tym eksperymencie. Przed użyciem w raporcie trzeba to uzupełnić.
- Obliczenie wykonano skryptem read-only poza workspace (`/tmp/analyze_partner.py`). Skrypt nie jest częścią repozytorium.

## Otwarte

- Definicja zamówienia dla poziomu zamówienia (P2).
- Przepis w `imports/recipes/` po zatwierdzeniu.
- Progi jakości w profilach.
