# BC-07 — Atrybuty produktu z opisów dostawców: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Automatyczne wypełnianie atrybutów produktu (`Ocieplenie`, `Wodoodpornosc`, `MaterialGlowny`) z opisów dostawców.
- Porównanie: reguły i parser składu, TF-IDF + regresja logistyczna, osadzenia zdań + regresja logistyczna, model językowy przez API (format JSON, walidacja schematu).
- Kluczowe zagadnienia: asymetria kosztu błędów, tryb z przeglądem niepewnych (krzywa pokrycie–jakość), przeciek formatu dostawcy (walidacja po dostawcach), przesunięcie rozkładu (nowy dostawca), szum etykiet ręcznych, prawie-duplikaty, koszt i powtarzalność modelu językowego.
- Dane: 2 400 opisów, 400 zakodowanych ręcznie, 2 000 niezakodowanych; niezależne od danych sprzedażowych.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| Ręczne kodowanie ok. 2 min na opis; kolejka ok. 2 400 | Model kosztowy: czas ręczny vs koszt wywołań vs koszt błędów |
| Błędny filtr („wodoodporna" przy kurtce, która nie jest) kończy się reklamacjami; brak atrybutu jest mniej groźny | Asymetria błędów: precyzja klasy `tak` dla wodoodporności jako metryka krytyczna; progi pewności |
| „Czy warto, w jakim trybie?" | Rekomendacja per atrybut: automat, automat z przeglądem niepewnych, ręcznie |
| Etykiety ręczne wpisywane szybko przez trzy osoby | Szacowanie szumu etykiet i jego wpływu na ocenę |
| Nowe dostawy | Walidacja po dostawcach, walidacja adwersaryjna, plan próbki dla nowego dostawcy |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Merchandising operacyjny z e-commerce: opisy od dostawców w różnych formatach (czasem po angielsku); dziś atrybuty wpisywane ręcznie, ok. 2 minut na opis; w kolejce ok. 2 400 opisów, ręcznie zakodowano 400; atrybuty zasilają filtry i raporty; pytania: czy da się zautomatyzować, z jaką jakością, za jaką cenę, co z błędami.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; PLN. Kategorie: Kurtki, Sukienki, Swetry, Jeansy, T-shirty, Koszule, Akcesoria. Sezony SS i AW.
- Atrybuty i opisy są poza hurtownią sprzedażową.

**Tabele** (`datasets/synthetic/bc07/`):
- `product_texts`: `TextId`, `Supplier`, `Category`, `Description`.
- `labels_gold`: `TextId`, `Ocieplenie`, `Wodoodpornosc`, `MaterialGlowny` (ręczne etykiety).

**Ograniczenia dokumentowane.**
- Etykiety ręczne wpisywały trzy osoby; nie mierzono zgodności; brak drugiej weryfikacji.
- Opisy pochodzą od kilku dostawców o różnych szablonach.
- Prawdziwe etykiety zbioru niezakodowanego są nieznane.

**Zasady kodowania.**
- `Ocieplenie` ∈ {`tak`, `nie`, `brak_informacji`}: `tak` — opis stwierdza ocieplenie (ocieplana, watowana, puchowa, z ociepliną, ocieplana podszewka; insulated, padded, thermal lining); `nie` — opis wprost mówi, że produkt nie jest ocieplany albo nazywa go letnim/przejściowym bez ocieplenia; `brak_informacji` — opis nic nie mówi.
- `Wodoodpornosc` ∈ {`tak`, `czesciowo`, `nie_lub_brak`}: `tak` — wodoodporna, nieprzemakalna, waterproof; `czesciowo` — hydrofobowa, impregnowana, odporna na deszcz, water-repellent, DWR; `nie_lub_brak` — brak wzmianki lub wprost niewodoodporna.
- `MaterialGlowny` ∈ {`bawelna`, `welna`, `poliester`, `len`, `wiskoza`, `denim`, `skora_ekologiczna`, `inne`, `brak_informacji`}: materiał o największym udziale w podanym składzie (CO bawełna, WO wełna, PES/PL poliester, LI len, VI/CV wiskoza; PA, AC, EL i inne → `inne`); skład procentowy ma pierwszeństwo przed sformułowaniami marketingowymi („wełniany look"); bez składu wyraźne twierdzenie o materiale; `denim` tylko dla jeansów bez składu; `brak_informacji`, gdy opis nie pozwala ustalić.

**Definicje metryk.** Precyzja, czułość, F1 klasy; macro-F1; pokrycie (coverage); koszt na 1000 opisów.

**Środowisko.** Python, sentence-transformers (jeśli model dostępny), model językowy przez API (klucz ze zmiennej środowiskowej: `OPENAI_API_KEY` lub `ANTHROPIC_API_KEY`, nazwa modelu ze zmiennej `*_MODEL` lub zapisana wybrana); tylko prawdziwe wywołania.

**Produkty końcowe.** Notebook, raport 1 strona (tryb per atrybut, koszt, oczekiwany odsetek błędów na stronie, plan dla nowego dostawcy), kod reguł i parsera.

