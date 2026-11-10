# Słownik metryk Nordvik
Kwoty w PLN. Jeśli w mianowniku jest zero, wynik wskaźnika pozostaje pusty.
- Sprzedaż brutto: wartość sprzedanego towaru z VAT po rabacie. Źródło: FactSales.GrossAmount.
- Sprzedaż netto: sprzedaż brutto bez VAT (23%). Źródło: FactSales.NetAmount. Słowo „sprzedaż" bez doprecyzowania oznacza sprzedaż netto przed odjęciem zwrotów.
- Sztuki: SUM(FactSales.Quantity). Stopa rabatu: rabat / SUM(Quantity × UnitPrice).
- Liczba transakcji: COUNT(DISTINCT TransactionNo), nie COUNT(*). Średni koszyk: sprzedaż netto / liczba transakcji. UPT: sztuki / liczba transakcji.
- Koszt własny (COGS): SUM(Quantity × UnitCost).
- Marża brutto: sprzedaż netto − koszt własny − wartość zwrotów bez VAT przyjętych w tym samym okresie. Marża %: marża brutto / sprzedaż netto. Zwroty obniżają marżę okresu przyjęcia zwrotu.
- Wartość zwrotów netto: SUM(ReturnAmount) / 1,23. Wskaźnik zwrotów: sztuki zwrócone / sztuki sprzedane w tym samym okresie i przekroju. Zwrot ma datę i sklep przyjęcia.
- Przychód na m²: sprzedaż netto / powierzchnia sprzedaży, tylko sklepy stacjonarne. SalesAreaM2 to bieżąca powierzchnia; przy porównaniach sprzed i po przebudowie obie strony dzielone są przez dzisiejszą powierzchnię.
- Stan magazynowy: StockQuantity na koniec dnia, migawka (nie sumować stanów z kolejnych dni).
- Dostępność: udział SKU ze stanem > 0 wśród SKU objętych zapasem (obecnych w feedzie) na dzień i sklep. Nie obejmuje całego katalogu.
- Sell-through: sprzedane w sezonie / (sprzedane w sezonie + stan na koniec okresu).
- Tydzień handlowy: tydzień ISO-8601 (pn–nd); do grupowania używaj IsoYear z IsoWeek. Sezon SS: luty–lipiec, AW: sierpień–styczeń.
- Kanały: ONLINE i STORE (DimStore.Channel).
