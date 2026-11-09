# P01.04 — Dane partnera

**Od:** Marta, Merchandising  
**Temat:** AW — czy możemy potwierdzić dosyłkę?

```text
Przed spotkaniem zakupowym potrzebuję krótkiej oceny dostępności dla wybranych SKU i sklepów. Partner przesłał najnowsze eksporty. Czy możecie wskazać, które pozycje wyglądają na możliwe do potwierdzenia i gdzie termin może być ryzykowny? Nie traktujcie samej dostępności u partnera jako prognozy popytu. Jeśli kody lub definicje nie pozwalają połączyć danych, proszę zatrzymać rekomendację i wskazać, co musimy wyjaśnić. Żadna ilość nie jest jeszcze zatwierdzonym zamówieniem.
```

**Od:** Partner  
**Do:** Zespół DS

```text
„W załączniku znajdziecie zamówienia i stan dostępności. W kolumnie AvailableUnits raportujemy towar w migawce wskazanej datą AsOfDate. Przy planowaniu proszę patrzeć na ilość po rezerwacjach i MOQ. Daty dostawy są obecnym terminem obietnicy; status at_risk wymaga potwierdzenia z naszym zespołem. PartnerSKU jest naszym kodem jednostki asortymentowej. Nie gwarantujemy, że oba pliki były generowane w tej samej chwili.”
```

**Od:** Partner  
**Do:** Zespół DS

```text
„W `partner_shipments_v3` każda linia ma osobny PartnerLineId; linia opisuje SKU, destynację i tydzień. Termin jest obietnicą na moment eksportu. `partner_availability_v2` zawiera migawki dostępności z kilku kolejnych tygodni; rezerwacje odejmuje się od AvailableUnits przy planowaniu. Status `at_risk` nie oznacza anulowania. Nasze PartnerSKU obejmują szerszy katalog hurtowy; mapowanie wybranych SKU Nordvik jest w osobnym pliku asortymentowym. Niektóre komentarze są wpisywane ręcznie.”
```
