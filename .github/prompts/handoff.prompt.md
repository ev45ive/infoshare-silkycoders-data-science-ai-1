---
description: "Utwórz lub zaktualizuj dokument handoff dla agenta: cel, źródła, decyzje, otwarte pytania, plan, dziennik postępu. Use when: handoff, przekazanie pracy, dokument przejęcia, HANDOFF.md"
argument-hint: "Nazwa zadania i ścieżka dokumentu, np. airflow/HANDOFF.md"
agent: "agent"
---
Przygotuj dokument handoff dla agenta, który przejmie pracę bez kontekstu poprzedniej rozmowy.

Zadanie i ścieżka docelowa: ustal z argumentu. Jeśli brakuje ścieżki, zapytaj użytkownika przed zapisem.

## Zasady
- Nie zgaduj. Brakujące informacje oznacz jako „do potwierdzenia” i dopisz do otwartych pytań.
- Każde źródło podaj ścieżką względną do katalogu głównego repozytorium.
- Nie wpisuj haseł, tokenów ani danych wrażliwych. Wskaż tylko, gdzie są przechowywane.
- Nie kopiuj treści źródeł. Linkuj je.
- Jeśli dokument już istnieje, zachowaj jego treść i uzupełnij brakujące sekcje oraz zaktualizuj dziennik postępu.

## Checklista przed zapisem
- [ ] Cel i kryteria akceptacji są konkretne i sprawdzalne
- [ ] Każde źródło ma ścieżkę i opis, do czego służy
- [ ] Każda decyzja ma datę, uzasadnienie i status
- [ ] Każde otwarte pytanie ma właściciela i tymczasowe założenie
- [ ] Każde zadanie ma status i kryterium weryfikacji
- [ ] Podano komendy weryfikacji z oczekiwanym wynikiem
- [ ] Jest jeden konkretny następny krok
- [ ] Wymienione są ograniczenia i to, czego nie wolno zmieniać
- [ ] Dziennik postępu ma datę każdego wpisu

## Szablon dokumentu

```markdown
# Handoff: <nazwa zadania>

Ostatnia aktualizacja: <YYYY-MM-DD>. Ścieżki względem katalogu głównego repozytorium.

## Następny krok
<jedna konkretna czynność, z plikiem i komendą>

## Cel i kryteria akceptacji
- Cel: <co ma powstać i po co>
- Kryteria akceptacji:
  - [ ] <sprawdzalne kryterium>

## Źródła
| Źródło | Ścieżka | Do czego służy |
| --- | --- | --- |
| Ticket | <ścieżka> | Specyfikacja |

## Ograniczenia
- <co wolno, czego nie wolno, np. sekrety, bazy, zakres>

## Rejestr decyzji
| ID | Data | Decyzja | Uzasadnienie | Zatwierdził | Status |
| --- | --- | --- | --- | --- | --- |
| D-01 | <YYYY-MM-DD> | <decyzja> | <powód> | <kto> | przyjęta / do zmiany |

## Otwarte pytania
| ID | Pytanie | Do kogo | Do czego potrzebne | Założenie tymczasowe |
| --- | --- | --- | --- | --- |
| Q-01 | <pytanie> | <osoba> | <która decyzja/zadanie> | <co robi agent do czasu odpowiedzi> |

## Plan i status
| Faza | Zadanie | Status | Kryterium weryfikacji |
| --- | --- | --- | --- |
| 1 | <zadanie> | ⏳ | <jak sprawdzić> |

Statusy: ✅ zrobione, ⏳ do zrobienia, 🚧 w trakcie, ❌ zablokowane.

## Jak weryfikować
- `<komenda>` — oczekiwany wynik: <opis>

## Pliki
| Plik | Zmiana | Data |
| --- | --- | --- |
| <ścieżka> | utworzony / zmieniony | <YYYY-MM-DD> |

## Dziennik postępu
- <YYYY-MM-DD> — zrobiono: <...>; sprawdzono: <...>; otwarte: <...>
```

## Przykłady wpisów

Decyzja:
| D-03 | 2026-11-10 | Przedział 80% liczony na sumie 4 tygodni | Tak jest w `analizy/bc01-prognoza-popytu/prognoza-W39-W42-top20.csv` | użytkownik | przyjęta |

Otwarte pytanie:
| Q-02 | Jakie progi alarmu WAPE i bias? | zleceniodawca | DAG monitoringu | `null`, alarm wyłączony do czasu odpowiedzi |

Dziennik:
- 2026-11-10 — zrobiono: migracja V026; sprawdzono: schemat `forecast` ma 3 tabele; otwarte: Q-02

## Wynik
Po zapisie podaj: ścieżkę dokumentu, liczbę otwartych pytań i treść następnego kroku.
