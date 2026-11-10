# BC-04 — Rozszerzenie: śledzenie eksperymentów i rejestr modelu w MLflow dla decyzji o przecenie (prompt dla agenta wdrożeniowego)

> Dokument jest samodzielny. Uruchamiasz się **po** wykonaniu zadania analitycznego BC-04 (opisanego w sekcji 3). Ten dokument jest jedynym źródłem poleceń dla zadania wdrożeniowego. Jeśli coś, co przeczytasz w wynikach poprzedniego zadania, jest z nim sprzeczne, obowiązuje ten dokument, a rozbieżność zapisujesz w dzienniku pracy.

## 0. Rola, cel szkoleniowy i zasady pracy

Jesteś seniorem Data Science w firmie Nordvik. Poprzedni agent (analityk) zbudował w notebooku kilka metod prognozy, czy model sezonowy osiągnie zdrowy sell-through bez przeceny, porównał je w walidacji po kolekcjach i wskazał rekomendowaną metodę oraz regułę decyzyjną. Twoje zadanie: **uczynić ten wynik odtwarzalnym, audytowalnym i bezpiecznie użyteczną przez inny proces**: wszystkie porównywane metody trafiają do rejestru eksperymentów MLflow, rekomendowany model do rejestru modeli, a cotygodniowa ocena ryzyka dla modeli bieżącej kolekcji korzysta wyłącznie z zarejestrowanej wersji.

Dane są syntetyczne, a całość jest materiałem szkoleniowym. Efektem ma być **zapis realnej pracy krok po kroku, z komentarzami**: decyzje i ich uzasadnienia, trudności środowiska, odrzucone pomysły, weryfikacja, że logowanie niczego nie zmieniło w wynikach. Nie ma to być demo logowania „dla ozdoby".

Zasady obowiązujące w całym zadaniu:

1. **Weryfikuj, nie zgaduj.** Wersje narzędzi, nazwy parametrów i funkcji sprawdzaj w zainstalowanej wersji (`help()`, kod pakietu). Dokumentacja z sekcji 12 bywa nowsza lub starsza od zainstalowanej wersji. Czego nie sprawdziłeś, nie przedstawiaj jako faktu.
2. **Nie zmieniaj wyników poprzedniego zadania** (notebooka, raportu, danych). Wszystko nowe zapisuj w katalogu z sekcji 10. Błąd w poprzednich wynikach opisz w dzienniku, nie poprawiaj go po cichu.
3. **Nie edytuj istniejących plików** w `ds-ml-linux-setup/` ani w `databases/`. Jeśli potrzebna jest zmiana, opisz ją w `PROPOZYCJA_ZMIAN_SRODOWISKA.md` zamiast ją wykonywać.
4. **Ślepota na klucz.** Nie otwieraj katalogów `datasets/synthetic/_generatory/` i `datasets/synthetic/_klucze/`. To zadanie ich nie potrzebuje. Jeśli coś stamtąd zobaczysz przypadkiem, zapisz to w dzienniku.
5. **Sekrety.** Adresy usług i dane dostępowe tylko ze zmiennych środowiskowych (`os.getenv`). Nie wypisuj zawartości plików `.env`. **Do MLflow nie loguj sekretów ani zmiennych środowiskowych** (parametry i tagi są widoczne dla wszystkich użytkowników serwera).
6. **Decyzje przed kodem, dziennik po każdym kroku:** co zrobiłem, co zobaczyłem, co mnie zaskoczyło, co zdecydowałem i dlaczego, co odrzuciłem.
7. **Prostota.** Każdy log, tag, artefakt i komponent musi wskazywać pytanie, na które odpowiada. Nie dodawaj przeszukiwania hiperparametrów ani nowych metod po to, żeby było co śledzić. Złożoność dopiero po zmierzonej potrzebie.
8. **Bramki go/no-go.** Gdy narzędzie nie działa, masz limit dwóch prób diagnozy na jedną blokadę. Potem zapisz `BLOKADA.md` i przejdź do planu awaryjnego z sekcji 7 (E1).
9. **Uczciwość wyników.** Nie fabrykuj historii eksperymentów. Wyniki w rejestrze pochodzą z prawdziwych uruchomień wykonanych w tym zadaniu. Nie symuluj działania narzędzia.
10. **Reprodukowalność.** Ziarna losowe, wersje bibliotek, komendy uruchomienia w README. Notebook przechodzi „Restart & Run All" z wyjątkiem komórek wymagających działającej usługi (oznacz je). Komentarze tłumaczą „dlaczego". Język: polski.

## 1. Kontekst biznesowy: po co to jest

Nordvik to polska sieć odzieżowa z własną marką: 5 sklepów stacjonarnych i sklep internetowy, PLN. Kolekcje sezonowe (`SS`: luty–lipiec, `AW`: sierpień–styczeń) wchodzą w transzach. Cykl ceny modelu: pełna cena, po ok. 8 tygodniach od premiery rabat sezonowy −20…−30% (2–3 tygodnie), potem wyprzedaż −40…−60%. Decyzję o rabacie podaje dział cen dla każdego modelu osobno. **Przecena za wcześnie zabiera marżę, za późno zamraża zapas i wymusza głębszą wyprzedaż.**

Zlecenie (kierownik merchandisingu wspólnie z działem cen i promocji): ok. 7 tygodni po starcie kolekcji AW26 (modele wchodziły w trzech transzach: 3, 17 i 31 sierpnia 2026) chcą wiedzieć, które modele AW26 nie osiągną „zdrowego" sell-through do końca okresu pełnej ceny (roboczo: 60% w 8. tygodniu od premiery) i którym warto pomóc wcześniej. Poprzednie zadanie dostarczyło porównanie metod, rekomendowaną metodę z kalibracją, model kosztowy i regułę decyzyjną (kiedy flagować).

**Dlaczego MLflow, a nie dalej notebook:**
1. **Audytowalność.** Lista modeli do przeceny ma skutki finansowe. Dział cen musi móc odtworzyć, *która wersja modelu, na jakich danych i z jakimi parametrami* wskazała dany model. W notebooku to wynika z pamięci autora.
2. **Odtwarzalność porównania.** Każda metoda ma zapisane parametry, dane (wersja), metryki per kolekcja i wykres kalibracji w jednym miejscu, które może przejrzeć osoba spoza zespołu DS.
3. **Bezpieczne użycie przez inny proces.** Cotygodniowa ocena ryzyka nie importuje notebooka. Ładuje zarejestrowaną wersję modelu po aliasie i ma znany kontrakt wejścia i wyjścia.
4. **Kontrola zmian.** Nowa wersja modelu (po zakończeniu AW26 będą nowe etykiety) przechodzi sprawdzenia, zanim zmieni alias używany przez ocenę tygodniową.

**Czego MLflow nie robi:** nie poprawia modelu ani nie czyni go ważniejszym niż jest. Przy kilkudziesięciu zakończonych modelach rejestr nie zwiększa mocy wniosków. Nie obiecuj tego w raporcie.

## 2. Co ma powstać (wynik w języku biznesu)

(1) Eksperyment w MLflow z wszystkimi metodami z poprzedniego zadania, odtworzonymi na tej samej walidacji z identycznymi liczbami. (2) Zarejestrowany model rekomendowany przez poprzednie zadanie z kontraktem wejścia i wyjścia, kartą modelu (ograniczenia) i aliasem. (3) Skrypt cotygodniowej oceny modeli AW26, który ładuje model **wyłącznie po aliasie**, odmawia oceny poza zakresem, na którym model był uczony, i zapisuje listę z wersją modelu w nagłówku. (4) Runbook dla działu cen i krótki raport.

## 3. Wynik poprzedniego zadania, który dostajesz (wejścia)

Poprzednie zadanie (BC-04, sell-through i decyzja o wcześniejszej przecenie) powinno zostawić w katalogu `analizy/bc04-sell-through-przecena/`:
- `bc04-sell-through-przecena.ipynb`: definicja etykiety (sell-through w 8. tygodniu od premiery przy pełnej cenie, próg roboczo 60%), audyt (liczba zakończonych kolekcji i modeli, jakość stanów, rekonstrukcja dostaw), baseline'y (B0: częstość bazowa; B1/B2: ekstrapolacja tempa), metody (regresja logistyczna lub regresja sell-through, model gradientowy, opcjonalnie parametryczna krzywa sprzedaży), **walidacja po kolekcjach (leave-one-collection-out) i w czasie**, momenty decyzji, kalibracja, model kosztowy, wrażliwość na próg 50/60/70% i stosunek kosztów, lista modeli AW26 z ryzykiem, dziennik pracy.
- `raport-biznesowy.md`: lista modeli AW26 z rekomendacją, reguła decyzyjna, plan monitoringu.
- opcjonalnie `src/*.py`.

**Nie zakładaj, że to wszystko istnieje ani co dokładnie zawiera.** Przeczytaj i zapisz w dzienniku, czego brakuje oraz jaką wersję przyjmujesz.

Dane (Parquet, katalog `datasets/synthetic/bc04/`; dane do 2026-09-20; modele sezonowe kolekcji `SS25`, `AW25`, `SS26` zakończonych i `AW26` w toku; modele całoroczne nie są objęte):

| Plik | Ziarno | Kolumny |
| --- | --- | --- |
| `dim_date` | dzień | `DateKey`, `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth`, `IsoYear`, `IsoWeek`, `YearWeek`, `DayOfWeek`, `DayName`, `IsWeekend`, `Season` |
| `dim_store` | sklep (także online) | `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel`, `Format`, `SalesAreaM2`, `OpenedDate`, `RemodelDate` |
| `dim_product` | SKU | `ProductKey`, `SKU`, `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice`, `UnitCost`, `IsActive` |
| `merch_plan` | model | `StyleCode`, `Collection`, `LaunchDate` (planowana), `PlannedUnits` (plan zakupu, nie faktyczna dostawa) |
| `fact_sales` | pozycja paragonu lub zamówienia | `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId` |
| `fact_inventory_daily` | dzień × SKU × lokalizacja (migawka na koniec dnia) | `InventoryKey`, `DateKey`, `ProductKey`, `StoreKey`, `StockQuantity`, `LoadId` |

Fakty i definicje: stany magazynowe pochodzą z jednorazowego eksportu historycznego (jakość nieznana, zbadana przez poprzednie zadanie). `fact_inventory_daily` to migawka, nie sumuj stanów. Brak danych o dostawach i przesunięciach, brak historii cen (rabaty tylko w `DiscountAmount`). **Sell-through** = sztuki sprzedane w sezonie / (sztuki sprzedane w sezonie + stan na koniec okresu), liczony w obrębie jednego sezonu; w tym zadaniu narastająco od premiery modelu, sumowany po SKU i lokalizacjach modelu. Tydzień ISO grupuj po `IsoYear` razem z `IsoWeek`. `GrossAmount = Quantity × UnitPrice − DiscountAmount`, `NetAmount = GrossAmount / 1,23`.

Dane **zostają w Parquet**. Hurtownia PostgreSQL nie zawiera historii stanów ani katalogu sezonowego tego przypadku, więc w tym zadaniu bazy nie używasz.

## 4. Środowisko i narzędzia: fakty zweryfikowane w repozytorium i rzeczy do sprawdzenia

Fakty (źródła: `ds-ml-linux-setup/compose/compose.yaml`, `mlflow.Dockerfile`, `check-mlflow.py`, `workshop.sh`, `postgres-init.sh`, `.env.example`):
- Środowisko uruchamia `bash ds-ml-linux-setup/workshop.sh <akcja> <zestaw>`. Projekt Compose `ds-workshop`. Zestaw `core` to **PostgreSQL + MLflow**. `up` używa `--no-build`, a usługi mają `pull_policy: never`, więc obrazy muszą już istnieć (akcja `prepare`). Poświadczenia są w `ds-ml-linux-setup/compose/.env` tworzonym akcją `init` (publiczne, szkoleniowe; nie wypisuj zawartości pliku).
- MLflow: obraz `workshop-mlflow:3.5.0` zbudowany z `python:3.12-slim-bookworm` z **`mlflow==3.5.0`** (+ `psycopg2-binary`, `SQLAlchemy`). Serwer: `mlflow server --host 0.0.0.0 --port 5000 --workers 1 --serve-artifacts --artifacts-destination /mlartifacts --allowed-hosts "localhost:*,127.0.0.1:*,mlflow:5000"`. Magazyn metadanych: baza `mlflow` w PostgreSQL (rola `mlflow`). Artefakty: **przez serwer** (`--serve-artifacts`), w wolumenie `mlflow-artifacts`, więc klient potrzebuje tylko HTTP.
- Adresy: z hosta `http://127.0.0.1:5000` (port `${MLFLOW_PORT:-5000}`); z innych kontenerów projektu `http://mlflow:5000`. Lista `--allowed-hosts` jest ograniczona: żądanie z innym nagłówkiem hosta (np. inna nazwa) może zostać odrzucone.
- Repozytorium sprawdza MLflow skryptem `check-mlflow.py` **wykonywanym wewnątrz kontenera** (`workshop.sh check`). To nie jest test klienta z hosta ani wysyłania artefaktów z zewnątrz.
- Nazwa katalogu `ds-ml-linux-setup` wskazuje na Linux. Twój terminal może być na Windowsie (np. Git Bash z Docker Desktop). Sprawdź, co działa, i zapisz to.

Do sprawdzenia i zapisania w dzienniku: czy zestaw `core` już działa, wersja klienta MLflow w Twoim środowisku Pythona (**zainstaluj `mlflow==3.5.0`, tę samą co serwer**; różnica wersji klienta i serwera jest klasycznym źródłem niejasnych błędów), wersje `scikit-learn` i innych bibliotek modelu (wpisz do Setup, wersje z notebooka mają pierwszeństwo), adres serwera w zmiennej `MLFLOW_TRACKING_URI`.

**Plan awaryjny (kolejność):** (1) serwer środowiska; (2) jeśli niedostępny po dwóch próbach na blokadę: lokalny MLflow z backendem SQLite i lokalnym katalogiem artefaktów w katalogu zadania (rejestr modeli też działa; opisz, że to nie jest środowisko docelowe); (3) jeśli MLflow w ogóle nie da się użyć: tabela wyników w notebooku i model zapisany jako plik z opisanym kontraktem, a raport wprost mówi, że MLflow **nie został uruchomiony**.

## 5. Rozbieżności i uwagi do poprzedniego zadania (co uwzględniasz)

| # | Uwaga | Jak postępujesz |
| --- | --- | --- |
| 1 | **Zakres momentów decyzji vs wiek modeli AW26.** Poprzednie zadanie uczy i waliduje na momentach decyzji: końce tygodni 2–6 od premiery. W dniu odcięcia danych (2026-09-20) modele AW26 mają ok. 3, 5 i 7 tygodni (transze z 31 sierpnia, 17 sierpnia i 3 sierpnia). Model z transzy sierpniowej jest **poza zakresem uczenia**. | Skrypt oceny **odmawia** oceny modeli spoza zakresu momentów, na których model był walidowany (status „poza zakresem" z powodem), a nie ekstrapoluje. Zakres zapisujesz w oknie karty modelu i w tagach wersji. Nie zmieniasz po cichu modelu ani zakresu. Notujesz to jako pytanie do zleceniodawcy (czy rozszerzyć zakres na tydzień 7). |
| 2 | Liczba zakończonych modeli jest rzędu kilkudziesięciu (dokładną liczbę zapisał audyt poprzedniego zadania), a zakończona kolekcja `AW` jest jedna. Moc wniosków jest mała. | Rejestr nie zmienia tej mocy. Nie dodajesz przeszukiwania hiperparametrów ani nowych metod. Liczebność (ile modeli stoi za każdą liczbą) trafia do karty modelu. |
| 3 | Poprzednie zadanie wspominało o opcjonalnym logowaniu do MLflow, a wcześniejsza historia prób nie jest w rejestrze. | **Nie fabrykujesz historii.** Ponownie wykonujesz porównanie końcowe pod śledzeniem i sprawdzasz, że liczby są identyczne z notebookiem. Wcześniejsze ślepe uliczki z dziennika możesz odtworzyć jako osobne uruchomienia z tagiem „odrzucona ścieżka" i powodem, tylko jeśli kod do nich istnieje. |
| 4 | Etykieta w notebooku (sell-through w 8. tygodniu przy pełnej cenie) wymaga świadomej definicji wobec przecen w historii. | Definicję etykiety przepisz do karty modelu **dokładnie tak, jak w notebooku**. Nie zmieniaj jej. |
| 5 | Próg 60% i stosunek kosztów to założenia robocze, nie ustalenia biznesu. | Próg, koszty i wybrany próg decyzyjny zapisujesz jako **parametry** uruchomienia i tagi wersji modelu, żeby były widoczne przy audycie. |
| 6 | Kolejna kolekcja (AW26) zakończy się dopiero za miesiące i da nowe etykiety. | Runbook opisuje, kiedy i jak powstaje nowa wersja modelu i jakie sprawdzenia poprzedzają zmianę aliasu. |

## 6. Dane testowe i symulacje

Do testów kontraktu (zła kolejność kolumn, brakująca kolumna, wiek poza zakresem) używasz **ramek zbudowanych ręcznie** z jawnym oznaczeniem „test". Nie wyciągaj z nich wniosków o jakości modelu.

## 7. Przebieg pracy

Wykonuj etapy po kolei. W każdym zostaw w notebooku komentarz: decyzja, uzasadnienie, co zaskoczyło.

### E0 — Odczyt wejść i specyfikacja do zarejestrowania
- Przeczytaj notebook, raport i `src`. Zapisz **specyfikację**: lista metod (z nazwami), rekomendowana metoda, cechy (z definicją „tylko do końca tygodnia decyzji"), hiperparametry i ziarna, schemat walidacji (kolekcje, momenty decyzji), kalibracja, próg decyzyjny i model kosztowy.
- Zapisz **liczby referencyjne do odtworzenia** (Brier, log loss, AUC per metoda i per kolekcja, oczekiwany koszt decyzji, lista AW26 z ryzykiem) wraz z liczbą modeli stojących za każdą z nich.
- Zapisz, czego nie rejestrujesz i dlaczego (np. ślepe uliczki bez kodu).

### E1 — Brama środowiska (go/no-go)
1. Ustal system hosta i czy zestaw `core` działa (`bash ds-ml-linux-setup/workshop.sh status`). Jeśli nie, uruchom go (`up core`, po `init` i `prepare`, jeśli trzeba). Przeczytaj `compose.yaml`, `mlflow.Dockerfile`, `check-mlflow.py`.
2. Zainstaluj w środowisku projektu `mlflow==3.5.0`. Ustaw `MLFLOW_TRACKING_URI` na adres z hosta.
3. **Test z klienta (to, czego nie robi repozytorium):** utwórz eksperyment testowy, zaloguj parametr, metrykę i mały artefakt (np. wykres), wczytaj je z powrotem, zaloguj mały model i załaduj go ponownie. Zapisz komendy i wynik. Zwróć uwagę na błędy związane z nagłówkiem hosta i wersją.
4. Jeśli test nie przejdzie po dwóch próbach na blokadę, `BLOKADA.md` i plan awaryjny (sekcja 4).

### E2 — Konwencje śledzenia (notatka projektowa przed logowaniem; w notebooku, maksymalnie strona)
Zapisz i uzasadnij:
- **Nazwa eksperymentu** i konwencja nazw uruchomień (metoda, schemat walidacji, wersja danych).
- **Parametry:** metoda, cechy (lista lub wersja zestawu), hiperparametry, ziarno, schemat walidacji, próg sell-through, założenia kosztowe, momenty decyzji.
- **Metryki:** Brier, log loss, AUC i oczekiwany koszt decyzji, każda w wersji zbiorczej oraz **per kolekcja** (np. osobne metryki dla każdej kolekcji w walidacji), oraz liczba modeli stojących za metryką.
- **Artefakty:** wykres kalibracji, lista cech lub współczynniki, tabela prognoz walidacyjnych (małe pliki), nie surowe dane.
- **Tagi:** wersja danych (suma kontrolna plików wejściowych), wersja kodu (jeśli repozytorium ma historię; inaczej suma kontrolna modułu), zakres momentów decyzji, status (kandydat, odrzucona ścieżka), powód.
- **Zasada:** jedno uruchomienie na metodę z jej pełną walidacją. Uruchomienia zagnieżdżone dla foldów tylko, jeśli coś z nich czytasz. Automatyczne logowanie bibliotek (autolog) tylko, jeśli nie zaśmieca zapisu logowaniem każdego treningu w pętli walidacji; w razie wątpliwości loguj jawnie.
- **Czego nie logujesz:** sekretów, zmiennych środowiskowych, surowych danych.

### E3 — Powtórzenie porównania pod śledzeniem i parytet
- Uruchom każdą metodę z E0 na walidacji z poprzedniego zadania z logowaniem zgodnym z E2. Wynik wynosi tyle uruchomień, ile metod.
- **Parytet:** liczby w rejestrze = liczby z notebooka (przy tych samych ziarnach i wersjach bibliotek). Rozbieżność jest wynikiem zadania: zbadaj (ziarno, kolejność danych, wersja biblioteki, niedeterminizm) i opisz. Nie „dostrajaj", żeby się zgadzało.
- Dokumentuj, ile czasu zajmuje pełne porównanie (to wpływa na późniejszą aktualizację modelu).

### E4 — Porównanie w interfejsie i w kodzie
- Otwórz porównanie uruchomień w interfejsie MLflow i odtwórz tabelę porównawczą z poziomu kodu (wyszukiwanie uruchomień w eksperymencie). Sprawdź, czy wniosek jest taki sam jak w raporcie poprzedniego zadania (która metoda i dlaczego).
- Zapisz, co z tego ekranu zobaczyłby dział cen bez znajomości kodu i czego mu brakuje (np. opisy metod, liczebności).

### E5 — Pakowanie i rejestracja modelu
- Zaloguj **rekomendowaną** metodę jako model (z sygnaturą wejścia i wyjścia oraz przykładem wejścia). Jeśli rekomendacja nie jest estymatorem biblioteki (np. reguła z kalibracją), opakuj ją jako model ogólny z własną klasą (tak, by interfejs był jednolity: **cechy na wejściu, prawdopodobieństwo na wyjściu**). W MLflow 3.x nazwę logowanego modelu podaje się innym parametrem niż w 2.x (`name` zamiast `artifact_path`): sprawdź sygnaturę w zainstalowanej wersji.
- Zapisz do **karty modelu** (plik w artefaktach): definicję etykiety, zakres momentów decyzji, liczbę modeli i kolekcji uczących, kalibrację, próg i założenia kosztowe, znane ograniczenia (jedna zakończona kolekcja `AW`, jakość stanów, brak dostaw), oczekiwane wejście z jednostkami.
- Zarejestruj model w rejestrze. Dodaj do wersji tagi (m.in. wersja danych, zakres momentów decyzji, status walidacji). **Używaj aliasów** (np. kandydat, produkcyjny), nie etapów: aliasy są w dokumentacji opisane jako mechanizm wdrożeniowy; sprawdź status etapów w zainstalowanej wersji.

### E6 — Test konsumenta w czystym procesie
- W **osobnym procesie** (nie w notebooku): załaduj model po aliasie (`models:/<nazwa>@<alias>`), zbuduj wejście z danych i policz prawdopodobieństwa dla tych samych modeli i momentów co w notebooku. **Parytet z notebookiem.**
- Testy kontraktu: zła kolejność lub brak kolumny, wartość poza dopuszczalnym zakresem, wiek modelu poza zakresem momentów (sekcja 5, punkt 1). Zachowanie ma być jawne: czytelny błąd lub status „poza zakresem", nigdy cicha ekstrapolacja.
- Zmień alias na drugą wersję modelu (np. kandydata) i pokaż, że konsument ją podejmuje bez zmiany kodu, a po przywróceniu aliasu wraca do poprzedniej.

### E7 — Cotygodniowa ocena modeli bieżącej kolekcji
- Skrypt (`score_current_collection.py` lub podobny): wyznacza dla każdego modelu bieżącej kolekcji faktyczny wiek (od faktycznego startu sprzedaży), buduje cechy „as of" koniec ostatniego pełnego tygodnia, ładuje model po aliasie i zapisuje listę: model, wiek, status (oceniony lub poza zakresem), prawdopodobieństwo, rekomendacja wg reguły decyzyjnej z poprzedniego zadania, **w nagłówku pliku wersja modelu, wersja danych, data, parametry reguły**.
- Porównaj wynik z listą AW26 z notebooka dla modeli w zakresie: identyczna. Dla modeli poza zakresem: status i powód.

### E8 — Utrzymanie i zarządzanie zmianą
- **Runbook** dla działu cen: jak czytać listę, co znaczy „poza zakresem", kiedy nie ufać liście.
- **Cykl życia modelu:** kiedy powstanie nowa wersja (po zakończeniu AW26 będą nowe etykiety), jakie sprawdzenia poprzedzają zmianę aliasu (parytet na danych referencyjnych, Brier i kalibracja względem poprzedniej wersji, kontrola kontraktu), kto zmienia alias i jak wrócić do poprzedniej wersji.
- **Monitoring:** co porównujesz co tydzień (rozkład wejść względem uczenia, kalibracja po zakończeniu okresu pełnej ceny), jaki sygnał oznacza, że model przestał być wiarygodny.
- **Granice środowiska szkoleniowego:** jeden serwer, brak kontroli dostępu w rejestrze, publiczne poświadczenia, brak kopii zapasowych. Opisz, czego brakuje na produkcji.

### E9 — Raport i dziennik
- `raport-wdrozenia.md` (maks. 1 strona dla kierownika merchandisingu i działu cen): co zyskujemy względem samego notebooka (odtwarzalność, audyt, bezpieczne użycie), co w rejestrze **nie** zwiększa wiarygodności (mała liczba modeli), lista ocen z wersją modelu, ograniczenia i pytania otwarte.
- Dziennik pracy i pytania do zleceniodawcy z założeniami roboczymi (zakres momentów decyzji, próg 60%, kto zatwierdza zmianę aliasu).

## 8. Kryteria akceptacji (każde z dowodem w notebooku)

1. Test z klienta (E1): parametr, metryka, artefakt i model zapisane i odczytane z serwera, albo `BLOKADA.md` z użytym planem awaryjnym.
2. Parytet z notebookiem: metryki per metoda i per kolekcja w rejestrze identyczne z poprzednim zadaniem (lub rozbieżność wyjaśniona).
3. Każde uruchomienie ma parametry, wersję danych i kodu, metryki per kolekcja oraz liczebności. Brak sekretów w parametrach i tagach.
4. Rekomendowany model ma sygnaturę, kartę modelu, tagi wersji i alias.
5. Konsument w czystym procesie ładuje model po aliasie i odtwarza wyniki notebooka. Zmiana aliasu zmienia używaną wersję bez zmiany kodu.
6. Model odmawia oceny poza zakresem momentów decyzji z jawnym statusem, bez ekstrapolacji.
7. Lista ocen ma w nagłówku wersję modelu i wersję danych, a dla modeli w zakresie jest identyczna z listą z notebooka.
8. Środowisko: wersja klienta MLflow = wersja serwera, zapisane w Setup.

## 9. Pułapki

- ✗ Klient MLflow w innej wersji niż serwer (3.5.0). ✓ Ta sama wersja, test w E1.
- ✗ Uznanie, że `check-mlflow.py` w kontenerze sprawdza klienta z hosta. ✓ Własny test klienta (E1).
- ✗ Logowanie „retrospektywne", które udaje, że historia eksperymentów istniała. ✓ Powtórzone uruchomienia i jawna informacja, że wcześniejsze próby nie są w rejestrze.
- ✗ Dodawanie przeszukiwania hiperparametrów, by wypełnić rejestr. ✓ Tylko metody z poprzedniego zadania.
- ✗ Autolog w pętli walidacji, który zapisuje setki uruchomień. ✓ Jedno uruchomienie na metodę, jawne logowanie.
- ✗ Rejestracja modelu bez kontraktu wejścia i zakresu. ✓ Sygnatura, karta modelu, tagi wersji.
- ✗ Etapy zamiast aliasów jako mechanizm wdrożeniowy. ✓ Aliasy (po sprawdzeniu w zainstalowanej wersji).
- ✗ Ładowanie modelu po numerze wersji w skrypcie oceny. ✓ Po aliasie.
- ✗ Cicha ekstrapolacja dla wieku modelu spoza zakresu uczenia. ✓ Status „poza zakresem".
- ✗ Logowanie zmiennych środowiskowych, danych logowania lub surowych danych. ✓ Tylko parametry, metryki i małe artefakty.
- ✗ Wniosek „model jest lepszy”, bo jest w rejestrze. ✓ Liczebność modeli i przedziały w karcie modelu.
- ✗ Wypisywanie danych logowania lub zawartości `.env`. ✓ Zmienne środowiskowe.

## 10. Co oddajesz

Katalog `analizy/bc04-sell-through-przecena/mlflow/`:
1. `bc04-mlflow-wdrozenie.ipynb`. Sekcje w tej kolejności (zgodnie z zasadami notebooków projektu): Metadata & Purpose (autor: „agent AI, materiał szkoleniowy", data, zespół, cel, decyzje, wyniki), Setup (wersje, kontrola środowiska), Load Data (wejścia i dane), Explore (diagnoza środowiska i wejść), Transform (konwencje, pakowanie modelu), Analyze (parytet, porównanie, test konsumenta, ocena tygodniowa), Results & Conclusions, Appendix (Dziennik pracy, Decyzje i odrzucone opcje, Pytania do zleceniodawcy, Ograniczenia). Po wczytaniu danych wypisz wymiary i `head()`, wynik dłuższy niż 10 wierszy skracaj. Każdy wykres: tytuł, osie z jednostką, legenda przy wielu seriach.
2. `src/` (logowanie, opakowanie modelu, skrypt oceny), `tests/` (kontrakt i parytet), `README.md` (jak uruchomić serwer i skrypty, zmienne środowiskowe), `MODEL_CARD.md`.
3. `RUNBOOK.md`, `raport-wdrozenia.md`, w razie potrzeby `BLOKADA.md` i `PROPOZYCJA_ZMIAN_SRODOWISKA.md`.

Środowisko Pythona: sprawdź zainstalowane biblioteki, braki doinstaluj w środowisku projektu (nie globalnie), wersje wpisz do Setup.

## 11. Test seniora (sprawdź przed oddaniem) i czego unikać

Czy prawdziwy senior by tak pracował?
- Czy dział cen po raporcie wie, *która wersja modelu* wskazała dany model i jak to sprawdzić?
- Czy rejestr nie wywołuje fałszywego wrażenia mocy wniosków przy kilkudziesięciu modelach?
- Czy parytet z notebookiem sprawdzono na liczbach, a wersja klienta zgadza się z serwerem?
- Czy skrypt oceny odmawia tam, gdzie model nie był walidowany?
- Czy każdy log i tag odpowiada na realne pytanie audytora?
- Czy któryś krok jest sztucznie skomplikowany? Usuń go lub uzasadnij.
- Czy kto inny odtworzy całość z czystego środowiska?

Unikaj: rejestru pełnego uruchomień bez znaczenia; „pięknych" tabel porównawczych bez liczebności; ukrywania blokad środowiska; ozdobnych wykresów.

## 12. Źródła

- Rejestr modeli MLflow (modele, wersje, aliasy, tagi, URI `models:/<nazwa>@<alias>`): https://mlflow.org/docs/latest/ml/model-registry/
- Śledzenie MLflow: parametry, metryki, jawne logowanie modelu (`name=`), ładowanie modelu: https://mlflow.org/docs/latest/ml/tracking/quickstart/
- Pliki środowiska w repozytorium: `ds-ml-linux-setup/compose/compose.yaml`, `compose/mlflow.Dockerfile`, `compose/check-mlflow.py`, `compose/postgres-init.sh`, `compose/.env.example`, `workshop.sh`.
- Dokumentacja MLflow na stronie dotyczy najnowszej wersji. Serwer środowiska to 3.5.0: sprawdź zgodność sygnatur w zainstalowanej wersji klienta.
