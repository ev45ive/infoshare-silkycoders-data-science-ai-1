# Słownik lokalny P01.05

- `sales.csv`: wiersz = pozycja transakcji; `transaction_no + line_no` jest kluczem, `quantity` liczbą sztuk.
- `list_price_gross` zawiera VAT 23% przed rabatem; `discount_amount_gross` jest kwotą rabatu z VAT; `gross_amount` = ilość × cena po rabacie z VAT; `net_amount` = gross_amount / 1,23. Sprzedaż netto to suma `net_amount`.
- COGS = ilość × `unit_cost_net`; marża przed zwrotami = suma `net_amount` − COGS.
- `inventory_daily.csv`: ziarno SKU × sklep × dzień. Stan to migawka; nie sumować w czasie. W tych danych `opening_stock + receipts − sold_qty = closing_stock`.
- Sell-through wg definicji ogólnej to sztuki sezonu / (sztuki sezonu + stan końcowy), ale ten wyciąg nie obejmuje pełnego sezonu ani historii dostaw.
- Sprzedaż jest obserwowanym wynikiem, nie pełnym popytem; wyczerpany stan może ograniczyć sprzedaż.

Wartości w CSV są małym zestawem syntetycznym. Brak zwrotów, anulowań, transferów i sprzedaży utraconej; nie wyliczaj efektu przyczynowego rabatu ani pełnosezonowego sell-through.
