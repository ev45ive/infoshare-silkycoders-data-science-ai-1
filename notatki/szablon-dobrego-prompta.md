# 📋 SZABLON PROMPTA NA PRZYSZŁOŚĆ

## 1. **ROLA** (Context - for whom)
```
"Jesteś [zawód + seniority] pracujący w [organizacja]"
```
**Dlaczego?** → AI zaczyna z perspektywy eksperta, którego ekspertyzę masz. Tworzy realistyczne, trafne odpowiedzi zamiast generycznych.

---

## 2. **CEL** (What output)
```
"Cel: [konkretny efekt biznesowy, nie techniczny]"
```
**Dlaczego?** → AI wie **co dostarczyć**, nie trafia w pustkę. Cel != szczegóły implementacji.

---

## 3. **INSTRUKCJE** (Step by step)
```
"Instrukcje:
- zrób X, następnie Y
- uwzględnij Z"
```
**Dlaczego?** → Sekwencja kroków daje jasny plan działania. Bez instrukcji AI może robić to źle lub nie po kolei.

---

## 4. **ZASADY** (Constraints & guardrails)
```
"Zasady:
- używaj tylko narzędzi A i B
- nie czytaj dużych plików
- nie wychodzisz poza zakres X"
```
**Dlaczego?** → **Chroni od błędów**: kosztownych operacji, czytania niepotrzebnych danych, wychodzenia poza scope. Oszczędza tokeny i czas.

---

## 5. **FORMAT/STYL** (Output shape)
```
"Format: dokument .md w ./docs/
- sekcje markdown
- kody SQL w blokach ```sql"
```
**Dlaczego?** → Wiadomo **dokładnie co dostaniesz**. Unika niespodziewanych formatów (DOCX zamiast MD, kod nie w bloku, itd).

---

## 6. **KONTEKST BIZNESOWY** (Background knowledge)
```
"Inspiracja: Nordvik = sieć mody, 5 sklepów, ONLINE, 
przychód 78% STORE / 22% ONLINE, zwroty 4% / 18%"
```
**Dlaczego?** → Przykłady są **konkretne i stosowne**, nie abstrakcyjne. Przykład zwrotów 18% dla ONLINE brzmi realistycznie dla branży (nie generycy 5%).

---

## 7. **ITERACJA** (Refinement loop)
```
Druga wiadomość: "rozdziel na 2 pliki - osobno SQL, osobno Jupyter"
Trzecia: "dodaj CHANGELOG..."
```
**Dlaczego?** → **Szybkie iteracje bez restartu**. Ulepszanie przez feedback zamiast generowania od nowa. AI ma kontekst poprzednich krań.

---

## 🎯 CHECKLIST: Czy Twój prompt jest dobry?

- ✅ **Rola** — Jasne kim jestem / czym się zajmuję
- ✅ **Cel** — Wiem co chcę dostać (biznesowo, nie technicznie)
- ✅ **Instrukcje** — Mam plan kroków, nie zamieszanie
- ✅ **Zasady** — Wiem co jest **zakazane** (chroni i oszczędza)
- ✅ **Format** — Dokładnie gdzie i jak ma być kod/dokument
- ✅ **Kontekst** — Kolej przykłady dla branży, nie ogólnik
- ✅ **Zgłoszenie** — [#ticket/ref] dla śledzenia (opcjonalnie)

---

## 📌 Wzorzec na szybko:

```markdown
Rola: [kim jestem, doświadczenie]

Cel: [CO mam dostać, business outcome]

Instrukcje:
- Krok 1
- Krok 2

Zasady:
- używaj tylko [narzędzia A, B]
- nie czytaj [co nie wolno]
- nie rób [limity/excludes]

Format: [gdzie i jak: .md, SQL block, etc]

Kontekst: [branża, założenia biznesowe, przykłady realne]
```

---

## 💡 Dlaczego to działa?

**Bez tego:** "Wygoneruj dokumentację" → AI zgaduje, pali tokeny, trafia obok  
**Z tym:** AI ma mapę mapy, wiadomy kierunek, oszczędza i trafi 🎯

---

**Zapisz sobie ten szablon — będzie działać na każdy prompt!** 👍
