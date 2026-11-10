# Dokumentacja techniczna: asystent analityczny Nordvik (BC-09)

Dokumenty dla programisty, który ma zrozumieć **jak to działa i jak jest zbudowane bez czytania kodu**. Każdy dokument jest samodzielny, ale mają wspólny słownik (poniżej).

| Dokument | Odpowiada na pytanie | Czas czytania |
| --- | --- | --- |
| [architektura.md](architektura.md) | Z czego składa się całość, jak płynie pytanie i gdzie są granice bezpieczeństwa? | ok. 10 min |
| [rdzen-asystenta.md](rdzen-asystenta.md) | Jak działa sam asystent: narzędzia, kontrole SQL, dokumenty, prognoza, pętla, limity, warianty, oceniacz? | ok. 15 min |
| [usluga-struktura.md](usluga-struktura.md) | Jak działa usługa wokół rdzenia: API, graf z zatwierdzaniem, baza stanu, role, limity? | ok. 15 min |
| [uruchomienie-i-uzycie.md](uruchomienie-i-uzycie.md) | Jak uruchomić i używać usługi przez UI, REST API, MCP i narzędzia administracyjne? | ok. 15 min |
| [testy-automatyczne.md](testy-automatyczne.md) | Co sprawdzają testy automatyczne, czego nie sprawdzają i jak je uruchomić? | ok. 15 min |

Ścieżki czytania:

- **Chcę zrozumieć całość:** `architektura.md`, potem `rdzen-asystenta.md` i `usluga-struktura.md`.
- **Chcę to uruchomić i używać:** `uruchomienie-i-uzycie.md`.
- **Chcę zmieniać kod i nie zepsuć gwarancji:** `architektura.md` (sekcja „Rdzeń zamrożony"), potem `testy-automatyczne.md`.

## Słownik

| Pojęcie | Znaczenie |
| --- | --- |
| **Asystent** | Program, w którym model językowy odpowiada na pytania o dane i procedury Nordvik, korzystając z narzędzi. |
| **Rdzeń** | Kod asystenta w `src/asystent/` (narzędzia, prompty, pętla, limity). Został **zamrożony** przed testem końcowym analizy. |
| **Usługa** | Kod w `usluga/service/`, który udostępnia rdzeń wielu użytkownikom: logowanie, role, trwałe rozmowy, zatwierdzanie zadań. |
| **Narzędzie** | Funkcja, którą model może wywołać: `run_sql`, `search_docs`, `forecast`, `propose_task`. |
| **Pętla narzędzi** | Powtarzane wywołania modelu, w których model prosi o narzędzia, dostaje wyniki i odpowiada, gdy ma dość informacji. |
| **Wariant W1-W4** | Sposób zbudowania asystenta porównywany w analizie: W1 reguły bez modelu, W2 dokumenty bez liczb, W3 agent z narzędziami (wybrany), W4 orkiestrator z pod-agentami. |
| **Szkic zadania** | Zadanie przygotowane przez asystenta. Asystent **nie może** go zatwierdzić. |
| **Cztery oczy** | Zasada: zadanie zatwierdza człowiek z rolą `approver`, inny niż jego wnioskodawca. Egzekwowana w API i w bazie. |
| **Punkt kontrolny (checkpoint)** | Zapis stanu grafu w PostgreSQL; pozwala wstrzymać pytanie na zatwierdzenie i wznowić je nawet po restarcie usługi. |
| **Wstrzymanie (`interrupt`)** | Mechanizm LangGraph: graf zapisuje stan i czeka na decyzję człowieka. |
| **Zamrożenie** | Zapis sum kontrolnych i odcisków AST kodu przed testem końcowym: `wyniki/zamrozenie_konfiguracji.json`. |
| **Odcisk AST** | Skrót struktury kodu bez komentarzy; równość odcisku dowodzi, że zachowanie kodu jest to samo, mimo dopisanych komentarzy. |
| **Zbiór dev / test** | Pytania do strojenia (dev) i pytania testowe zapisane, ale jeszcze nieocenione (test, Faza 9 wstrzymana). |
| **Dziennik zużycia (ledger)** | Plik `cache/llm_zuzycie.json` z łączną liczbą zużytych tokenów (twardy limit 3 mln dla całego BC-09). |

## Powiązane dokumenty (poza tym katalogiem)

- Wnioski i dowody analizy: [../bc09-asystent-analityczny.ipynb](../bc09-asystent-analityczny.ipynb), raport dla biznesu: [../raport-biznesowy.md](../raport-biznesowy.md).
- Usługa: [../usluga/README.md](../usluga/README.md) (skrót uruchomienia), [../usluga/ADR.md](../usluga/ADR.md) (decyzje i model zagrożeń), [../usluga/RUNBOOK.md](../usluga/RUNBOOK.md) (operacje), [../usluga/raport-wdrozenia.md](../usluga/raport-wdrozenia.md) (raport), [../usluga/bc09-usluga.ipynb](../usluga/bc09-usluga.ipynb) (dowody).
- Dane i słownik metryk: `datasets/synthetic/bc09/` (w tym `slownik_metryk.md`) oraz [../../../docs/slownik-metryk.md](../../../docs/slownik-metryk.md).

## Czego te dokumenty nie obejmują

- Wyników jakościowych analizy (poprawność wariantów, hipotezy H1-H5): są w notebooku i raporcie, a nie tutaj, bo zmieniają się z przebiegiem; tu opisano **mechanizmy**.
- Oceny zbioru testowego (Faza 9) i ślepej oceny 20 odpowiedzi: wstrzymane do decyzji zleceniodawcy.
- Adaptera do PostgreSQL dla danych asystenta (dane zostają w DuckDB; adapter jest odłożony, patrz [../usluga/ADR.md](../usluga/ADR.md)).
