# Karta modelu: bc04-sell-through-risk (metoda M1a)

**Status: kandydat do przeglądu, NIE rekomendacja.** M1a to metoda główna wskazana z góry w fazie 6 notebooka BC-04. W walidacji po kolekcjach ma Brier 0.133 i jest **gorsza** niż prosta ekstrapolacja B1. Rekomendacja z fazy 8 oryginału nie powstała.

## Co przewiduje (etykieta, dokładnie jak w notebooku)
`risk = 1`, gdy sell-through narastający modelu (`StyleCode`, cała sieć) w dniu 55 od pierwszej faktycznej sprzedaży (koniec 8. tygodnia) jest niższy niż próg τ = 60%. Sell-through = sprzedane / (sprzedane + stan), narastająco od premiery, sumowany po SKU i lokalizacjach. Populacja: modele bez rabatu do dnia 55 (66 z 72; 6 przecenionych od dnia 42 wykluczono, bo ich etykieta jest zmieszana z rabatem).

## Wejście (kolejność nieistotna, nazwy obowiązkowe)
| Cecha | Jednostka / definicja |
|---|---|
| `pred55` | ekstrapolacja liniowa sell-through na dzień 55 z tempa ostatnich 14 dni [udział 0-1] |
| `st_d` | sell-through narastający w dniu decyzji [udział 0-1] |
| `trend` | ln((sprzedaż 7 dni + 1) / (sprzedaż 7 dni wcześniej + 1)) [bez jednostki] |
| `avail_core` | udział SKU w rozmiarach M, L, ONE ze stanem > 0 w sieci [udział 0-1]; w uczeniu bez zmienności, współczynnik = 0 |
| `restock` | supply_d / supply_0 - 1: uzupełnienia dostaw do dnia decyzji [udział] |
| `ln_price` | ln(cena netto modelu w PLN) |
| `k` | tydzień decyzji od pierwszej sprzedaży (liczba całkowita) |

Cechy liczone wyłącznie z danych do końca dnia decyzji. Definicje: notebook BC-04, sekcja „Transform: tabela modelowa”.

## Wyjście
Tabela: `p_risk` (prawdopodobieństwo `risk = 1`, 0-1; NaN poza zakresem) i `status` (`ok` albo `poza zakresem: <powód>`).

## Zakres ważności
- Tygodnie decyzji `k` = 2-7 (dni 13-48). Inny `k` zwraca status „poza zakresem”, bez ekstrapolacji.
- Cecha poza przedziałem widzianym w uczeniu także daje „poza zakresem”: {"pred55": [0.15864365728125945, 1.0], "st_d": [0.03966091432031486, 0.7964568413117226], "trend": [-0.749500117111077, 0.6123858239154869], "restock": [0.0, 0.3981181051265412], "ln_price": [3.45654747674532, 6.044889713781562]}. Dla `avail_core` nie ma przedziału (stała w uczeniu).
- Wartość spoza [0, 1] w `pred55`, `st_d`, `avail_core`, brak kolumny lub NaN: błąd (ValueError), nie wynik.

## Uczenie i walidacja
- Uczenie: regresja logistyczna (StandardScaler + L2, C = 1), 66 modeli z kolekcji SS25, AW25, SS26 (21 / 22 / 23), 396 wierszy model x moment. Ziarno 20260920.
- Walidacja po kolekcjach (LOCO, wartości out-of-fold z uruchomienia `2db39965aee84c82b03b7fb8300d0ca4`): Brier 0.133 [0.104; 0.166], log loss 0.466, AUC 0.885, ECE (5 przedziałów) 0.124. Brier per kolekcja: SS25 0.115, AW25 0.158, SS26 0.126. Przedział: bootstrap po modelach, 90%.
- Kalibracja: brak osobnej kalibracji (surowe wyjście regresji logistycznej). Wykres: artefakt `calibration.png` w uruchomieniu walidacyjnym.
- Próg decyzyjny i założenia kosztowe (parametry uruchomienia): δ = 20%, Δ = 25 p.p., h = 1,5%/mies., m = 2, ε = 50%, τ = 60%. **Próg decyzyjny dla tego modelu nie jest ustalony** (wymagałby fazy 8 oryginału).

## Znane ograniczenia
- Jedna zakończona kolekcja AW (AW25, 22 modele); kurtki i swetry (większość AW26) mają w historii dokładnie jedną kolekcję. Moc wniosków jest mała, a przedziały szerokie.
- Stany magazynowe pochodzą z jednorazowego eksportu o nieznanej jakości (99,9% spójności ze sprzedażą w audycie), brak danych o dostawach (uzupełnienia widać tylko jako wzrost stanu).
- W foldzie AW25 błąd jest wyraźnie większy (Brier 0.158) niż w SS25 i SS26.
- Model uczony na wszystkich 66 modelach; metryki walidacyjne dotyczą wersji uczonych bez testowanej kolekcji, nie tego samego obiektu.
- Modele AW26 z transzy sierpniowej (wiek > 7 tygodni) są poza zakresem; czy rozszerzyć zakres, to pytanie do zleceniodawcy.

## Wersje
Dane: sha256 d04194d8bdf4936a; kod: commit 312178c, `bc04_core.py` sha256 eb7950e59f4aeca7.
