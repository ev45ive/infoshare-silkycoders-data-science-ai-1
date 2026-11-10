# BC-07 — opisy produktów od dostawców (dane do ćwiczenia)

Dane syntetyczne firmy Nordvik (polska sieć odzieżowa: 5 sklepów stacjonarnych i sklep internetowy). Opisy produktów pochodzą od kilku dostawców i trafiają do kolejki merchandisingu, gdzie ręcznie uzupełnia się atrybuty produktu. Część opisów została już zakodowana ręcznie, reszta czeka w kolejce. Dane nie zawierają informacji o sprzedaży i nie łączą się z hurtownią sprzedażową.

## Pliki

| Plik | Zawartość |
| --- | --- |
| `product_texts.parquet` | Wszystkie opisy (2 400 wierszy) |
| `labels_gold.parquet` | Atrybuty zakodowane ręcznie (400 wierszy, podzbiór `TextId` z `product_texts`) |
| `README_dane.md` | Ten opis |

## Słownik danych

**`product_texts`**

| Kolumna | Typ | Opis |
| --- | --- | --- |
| `TextId` | tekst | Identyfikator opisu (np. `TX-000123`), unikalny, kolejność wierszy nie niesie informacji |
| `Supplier` | tekst | Kod dostawcy opisu: `DOST-A`, `DOST-B`, `DOST-C`, `DOST-D` |
| `Category` | tekst | Kategoria produktu: Kurtki, Swetry, Sukienki, Jeansy, T-shirty, Koszule, Akcesoria (torebki i szaliki) |
| `Description` | tekst | Treść opisu od dostawcy (PL, EN lub mieszana, różna długość i format) |

**`labels_gold`**

| Kolumna | Typ | Opis |
| --- | --- | --- |
| `TextId` | tekst | Klucz łączący z `product_texts` |
| `Ocieplenie` | tekst | `tak`, `nie`, `brak_informacji` |
| `Wodoodpornosc` | tekst | `tak`, `czesciowo`, `nie_lub_brak` |
| `MaterialGlowny` | tekst | `bawelna`, `welna`, `poliester`, `len`, `wiskoza`, `denim`, `skora_ekologiczna`, `inne`, `brak_informacji` |

## Liczebności

- 2 400 opisów, z czego 400 zakodowanych ręcznie (`labels_gold`) i 2 000 bez atrybutów.
- Dostawcy: `DOST-A`, `DOST-B`, `DOST-C`, `DOST-D`.
- Kategorie: Kurtki, Swetry, Sukienki, Jeansy, T-shirty, Koszule, Akcesoria.

## Zasady kodowania

| Atrybut | Wartości | Zasada |
| --- | --- | --- |
| `Ocieplenie` | `tak`, `nie`, `brak_informacji` | `tak`: opis stwierdza ocieplenie (ocieplana, watowana, puchowa, z ociepliną, ocieplana podszewka; po angielsku insulated, padded, thermal lining). `nie`: opis wprost mówi, że produkt nie jest ocieplany (np. „bez ocieplenia", „nieocieplana") albo nazywa go letnim/przejściowym bez ocieplenia. `brak_informacji`: opis nie mówi nic o ociepleniu |
| `Wodoodpornosc` | `tak`, `czesciowo`, `nie_lub_brak` | `tak`: opis stwierdza wodoodporność (wodoodporna, nieprzemakalna, waterproof). `czesciowo`: ograniczona odporność na wodę (hydrofobowa, impregnowana, odporna na deszcz, water-repellent, DWR). `nie_lub_brak`: brak wzmianki albo wprost niewodoodporna |
| `MaterialGlowny` | `bawelna`, `welna`, `poliester`, `len`, `wiskoza`, `denim`, `skora_ekologiczna`, `inne`, `brak_informacji` | Materiał o największym udziale w podanym składzie procentowym (kody: CO bawełna, WO wełna, PES lub PL poliester, LI len, VI lub CV wiskoza; PA poliamid, AC akryl, EL elastan i inne → `inne`). Skład procentowy ma pierwszeństwo przed sformułowaniami marketingowymi („wełniany look"). Bez składu: wyraźne twierdzenie w opisie o materiale (np. „z miękkiej wełny merino" → `welna`). `denim` tylko dla jeansów bez podanego składu. `brak_informacji`, gdy opis nie pozwala ustalić |

## Ostrzeżenie o jakości etykiet

Etykiety w `labels_gold` wpisywały ręcznie trzy osoby. Zgodności między nimi nie mierzono, więc nie wiadomo, jak często ich oceny się rozmijają. Traktuj je jako ocenę ręczną, nie jako prawdę absolutną.
