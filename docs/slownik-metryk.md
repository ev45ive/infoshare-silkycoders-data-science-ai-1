# Słownik metryk Nordvik

Definicje używane w raportach sprzedaży, rentowności i zapasu. Kwoty podajemy w PLN, a udziały i dynamiki w procentach. Metryki liczymy dla wskazanego okresu i przekroju; jeśli w mianowniku jest zero, wynik wskaźnika pozostaje pusty.

## Sprzedaż

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Sprzedaż brutto** | Wartość sprzedanego towaru z VAT, po rabacie. | `FactSales.GrossAmount` |
| **Rabat** | Kwota obniżki udzielonej na pozycjach sprzedaży. | `FactSales.DiscountAmount` |
| **Sprzedaż netto** | Sprzedaż brutto bez VAT; dla odzieży obowiązuje 23% VAT. | `FactSales.NetAmount` |
| **Sztuki** | Liczba sprzedanych sztuk. | `FactSales.Quantity` |
| **Wartość przed rabatem** | Wartość towaru według ceny sprzedaży przed obniżką, z VAT. | `SUM(FactSales.Quantity * FactSales.UnitPrice)` |
| **Stopa rabatu** | Rabat / wartość przed rabatem. | `FactSales` |
| **Średnia cena netto sztuki** | Sprzedaż netto / sztuki. | `FactSales` |
| **Udział kanału w sprzedaży** | Sprzedaż netto kanału / sprzedaż netto wszystkich kanałów w tym samym okresie. | `FactSales` + `DimStore.Channel` |
| **Zmiana sprzedaży tydzień do tygodnia** | (Sprzedaż netto bieżącego pełnego tygodnia − sprzedaż netto poprzedniego pełnego tygodnia) / sprzedaż netto poprzedniego tygodnia; oba tygodnie w tym samym przekroju. | `FactSales` + `DimDate` |
| **Sprzedaż po zwrotach netto** | Sprzedaż netto − wartość zwrotów bez VAT przyjętych w tym okresie. | `FactSales.NetAmount`, `FactReturns.ReturnAmount` |
| **Aktywne SKU** | Liczba różnych SKU sprzedanych w okresie. | `FactSales.ProductKey` |
| **Sztuki na aktywne SKU** | Sztuki / liczba aktywnych SKU. | `FactSales` |

W raportach zarządczych słowo **„sprzedaż”** bez doprecyzowania oznacza **sprzedaż netto**, przed odjęciem zwrotów. Sprzedaży brutto używamy, gdy pytanie dotyczy kwoty zapłaconej przez klienta.

Kanały to `ONLINE` i `STORE` z `DimStore.Channel`.

## Rentowność

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Koszt własny (COGS)** | Koszt sprzedanych sztuk: `SUM(Quantity * UnitCost)`. | `FactSales` |
| **Marża brutto** | Sprzedaż netto − koszt własny − wartość zwrotów bez VAT przyjętych w tym samym okresie. | `FactSales`, `FactReturns` |
| **Marża %** | Marża brutto / sprzedaż netto. | Jak wyżej |
| **Średni koszt sprzedanej sztuki** | Koszt własny / liczba sprzedanych sztuk. | `FactSales` |
| **Udział kosztu własnego w sprzedaży** | Koszt własny / sprzedaż netto. | `FactSales` |

Zwroty obniżają marżę okresu **przyjęcia zwrotu**, nie okresu pierwotnej sprzedaży. `FactReturns.ReturnAmount` jest kwotą z VAT; wartość zwrotów w definicji marży podajemy bez VAT.

## Transakcje i koszyk

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Liczba transakcji** | Liczba unikalnych paragonów: `COUNT(DISTINCT TransactionNo)`. | `FactSales` |
| **Średni koszyk** | Sprzedaż netto / liczba transakcji. | `FactSales` |
| **UPT** (units per transaction) | Sztuki / liczba transakcji. | `FactSales` |

## Produktywność sklepu

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Przychód na m²** | Sprzedaż netto / powierzchnia sprzedaży; liczony osobno dla sklepów stacjonarnych. | `FactSales`, `DimStore.SalesAreaM2` |

`DimStore.SalesAreaM2` zawiera **bieżącą** powierzchnię. Przy porównaniu sprzed i po przebudowie (`DimStore.RemodelDate`) obie strony są dzielone przez dzisiejszą powierzchnię. Kanał online nie ma powierzchni sprzedaży.

## Zapas i dostępność

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Stan magazynowy** | Liczba sztuk na koniec dnia handlowego dla SKU w sklepie. | `FactInventoryDaily.StockQuantity` |
| **Dostępność** | Udział SKU ze stanem > 0 wśród SKU objętych zapasem na dany dzień i sklep. | `FactInventoryDaily` |
| **Sell-through** | Sztuki sprzedane w sezonie / (sztuki sprzedane w sezonie + stan na koniec okresu). | `FactSales`, `FactInventoryDaily` |
| **SKU dostępne** | Liczba SKU ze stanem > 0 w zgłoszonym zapasie dla dnia i sklepu. | `FactInventoryDaily` |
| **SKU niedostępne** | Liczba SKU ze stanem ≤ 0 w zgłoszonym zapasie dla dnia i sklepu. | `FactInventoryDaily` |
| **Wartość zapasu w koszcie** | Suma stanu sztuk × bieżący koszt jednostkowy SKU na wybrany dzień. | `FactInventoryDaily`, `DimProduct.UnitCost` |

Stan jest **migawką**, więc nie sumujemy stanów z kolejnych dni. Dostępność obejmuje SKU obecne w feedzie zapasu, nie cały katalog `DimProduct`. Wartość zapasu używa bieżącego kosztu z wymiaru, więc nie jest historyczną wyceną księgową. Sell-through liczymy w obrębie jednego sezonu, zestawiając sprzedaż i stan z tego samego zakresu; feed zapasu obejmuje tylko bieżący sezon.

## Zwroty

| Metryka | Definicja | Źródło |
| --- | --- | --- |
| **Wskaźnik zwrotów** | Sztuki zwrócone / sztuki sprzedane w tym samym okresie i przekroju. | `FactReturns`, `FactSales` |
| **Sztuki zwrócone** | Liczba sztuk przyjętych jako zwrot w okresie. | `SUM(FactReturns.Quantity)` |
| **Wartość zwrotów netto** | Wartość przyjętych zwrotów bez VAT. | `SUM(FactReturns.ReturnAmount) / 1.23` |

Powody zwrotów: `DAMAGED`, `WRONG_SIZE`, `CHANGED_MIND`, `OTHER`. Kanały porównujemy osobno, bo udział zwrotów online jest zwykle większy. Data i sklep w `FactReturns` oznaczają **przyjęcie zwrotu**; nie zakładaj, że to data i kanał pierwotnej sprzedaży.

## Kalendarz

- **Tydzień handlowy:** pełny tydzień ISO-8601 od poniedziałku do niedzieli; `DimDate.YearWeek` ma format np. `2026-W24`.
- **Rok ISO:** na przełomie roku może różnić się od roku kalendarzowego. Do grupowania tygodni używaj `IsoYear` razem z `IsoWeek`, nigdy `Year` z `IsoWeek`.
- **Sezon:** `SS` obejmuje luty–lipiec, a `AW` sierpień–styczeń, np. `AW26`.
