# Jupyter Notebook: Dokumentacja i przykłady analiz

*Dokument zawiera szablony, strukturę i kompletny przykładowy notebook dla zespołu Data Science w Nordvik.*

---

## Spis treści

1. [CHANGELOG](#changelog)
2. [Struktura notebooka Jupyter](#struktura-notebooka-jupyter)
3. [Szablonowe sekcje](#szablonowe-sekcje)
4. [Kompletny przykładowy notebook](#kompletny-przykładowy-notebook)
5. [Checklist Jupyter](#checklist-jupyter)

---

## CHANGELOG

| Data | Autor | Ticket | Model AI | Zmiana |
|------|-------|--------|----------|--------|
| 2026-11-09 | Olek | [#zgloszenia/01](../zgloszenia/01.md) | Claude 3.5 Sonnet | Dokument utworzony: struktura notebooka + 8 szablonowych sekcji + example notebook "Analiza zwrotów Online vs Store" |
| | | | | |

**Format wpisu:** `YYYY-MM-DD | Imię Nazwisko | [#ticket] | Model/brak | Czego zmieniono i dlaczego w jednej linii, konkretnie**

---

## Struktura notebooka Jupyter

Każdy notebook powinien mieć następującą strukturę:

```
1. [Metadata & Purpose] — krótka komórka markdown
2. [Setup] — importy, konfiguracja, połączenie z bazą
3. [Load Data] — pobranie danych SQL lub z cache
4. [Explore] — EDA, profiling, anomalie
5. [Transform] — czyszczenie, feature engineering
6. [Analyze] — wizualizacje, testy statystyczne
7. [Results & Conclusions] — wyniki i rekomendacje
8. [Appendix] — kod pomocniczy, edge cases
```

---

## Szablonowe sekcje

### Sekcja 1: Metadata & Purpose

```markdown
# Analiza: Wpływ promocji na sprzedaż w sezonie AW26

**Autor:** Anna Kowalska  
**Data:** 2026-11-09  
**Zespół:** Data Science  
**Status:** ✅ Zakończona  

## Cel
Zbadać, czy kampania promocyjna w tygodniu 44 (26-31 października) miała 
istotny statystycznie wpływ na przyrost sprzedaży i retention rate.

## Główne hipotezy
1. Sprzedaż wzrosła o min. 20% w tygodniu promocji
2. Zwrot na online był wyższy niż normalnie (wynik promocji: nieświadomi klienci)
3. Efekt miał miejsce głównie w ONLINE, mniej w STORE

## Wyniki (TL;DR)
✅ Hipoteza 1: POTWIERDZONA (wzrost 28%)  
❌ Hipoteza 2: FALSZYWA (zwroty na poziomie baseline)  
✅ Hipoteza 3: POTWIERDZONA (73% wzrostu online vs 12% store)
```

### Sekcja 2: Setup

```python
# Setup

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import os

warnings.filterwarnings('ignore')

# Style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 11

# Database connection (example: SQL Server)
import pyodbc
import sqlalchemy as sa

DB_SERVER = "nordvik-analytics.database.windows.net"
DB_NAME = "nordvik_dw"
DB_USER = "ds_read_user"
# Password from environment variable (NEVER hardcode!)
DB_PASSWORD = os.getenv('NORDVIK_DB_PASSWORD')

connection_string = (
    f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:1433/{DB_NAME}?"
    f"driver=ODBC+Driver+17+for+SQL+Server"
)
engine = sa.create_engine(connection_string)

print(f"✓ Connection established to {DB_NAME}")
```

### Sekcja 3: Load Data

```python
# Load Data

query = """
SELECT
    t.sale_date,
    s.store_name,
    s.channel,
    COUNT(DISTINCT t.transaction_id) AS transactions,
    SUM(CASE WHEN t.quantity > 0 THEN t.amount ELSE 0 END) AS sales_pln,
    SUM(CASE WHEN t.quantity < 0 THEN ABS(t.quantity) ELSE 0 END) AS returns_qty
FROM sales.transactions t
INNER JOIN master.stores s ON t.store_id = s.store_id
WHERE t.sale_date BETWEEN '2026-10-15' AND '2026-11-09'
    AND t.transaction_status = 'COMPLETED'
GROUP BY t.sale_date, s.store_name, s.channel
"""

df_sales = pd.read_sql_query(query, engine)
df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'])

print(f"✓ Loaded {len(df_sales)} rows")
print(f"Date range: {df_sales['sale_date'].min().date()} to {df_sales['sale_date'].max().date()}")
print(f"Stores: {df_sales['store_name'].unique().tolist()}")
```

### Sekcja 4: Explore

```python
# Explore Data

print("Shape:", df_sales.shape)
print("\nFirst rows:")
print(df_sales.head(10))

print("\nData types:")
print(df_sales.dtypes)

print("\nMissing values:")
print(df_sales.isnull().sum())

print("\nBasic statistics:")
print(df_sales[['transactions', 'sales_pln', 'returns_qty']].describe())

# Anomalies
print("\nAnomalies:")
print(f"- Dates with 0 transactions: {(df_sales['transactions'] == 0).sum()}")
print(f"- Negative sales: {(df_sales['sales_pln'] < 0).sum()}")
```

### Sekcja 5: Transform

```python
# Transform

# Add derived columns
df_sales['week_number'] = df_sales['sale_date'].dt.isocalendar().week
df_sales['dow'] = df_sales['sale_date'].dt.day_name()
df_sales['is_promotion_period'] = (
    (df_sales['sale_date'].dt.isocalendar().week == 44) &
    (df_sales['sale_date'].dt.year == 2026)
)

# Baseline (pre-promotion average)
baseline_sales = df_sales[~df_sales['is_promotion_period']]['sales_pln'].mean()
df_sales['sales_vs_baseline_pct'] = (
    (df_sales['sales_pln'] - baseline_sales) / baseline_sales * 100
).round(2)

print(f"Baseline daily sales (avg): {baseline_sales:,.0f} PLN")
print(f"\nPromotion period ({df_sales[df_sales['is_promotion_period']].shape[0]} rows):")
print(df_sales[df_sales['is_promotion_period']][
    ['sale_date', 'channel', 'sales_pln', 'sales_vs_baseline_pct']
])
```

### Sekcja 6: Analyze

```python
# Analyze: Sales Lift by Channel

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 1: Daily sales trend
for channel in df_sales['channel'].unique():
    channel_data = df_sales[df_sales['channel'] == channel]
    axes[0].plot(
        channel_data['sale_date'],
        channel_data['sales_pln'],
        marker='o',
        label=channel,
        linewidth=2
    )

# Highlight promotion period
promo_start = pd.Timestamp('2026-10-26')
promo_end = pd.Timestamp('2026-10-31')
axes[0].axvspan(promo_start, promo_end, alpha=0.2, color='yellow', label='Promotion')
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Sales (PLN)')
axes[0].set_title('Daily Sales by Channel (with promotion highlight)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Chart 2: Sales lift % by channel during promotion
promo_df = df_sales[df_sales['is_promotion_period']]
non_promo_df = df_sales[~df_sales['is_promotion_period']]

lift_by_channel = []
for channel in df_sales['channel'].unique():
    promo_avg = promo_df[promo_df['channel'] == channel]['sales_pln'].mean()
    non_promo_avg = non_promo_df[non_promo_df['channel'] == channel]['sales_pln'].mean()
    lift_pct = ((promo_avg - non_promo_avg) / non_promo_avg * 100)
    lift_by_channel.append({'channel': channel, 'lift_pct': lift_pct})

lift_df = pd.DataFrame(lift_by_channel)
axes[1].bar(lift_df['channel'], lift_df['lift_pct'], color=['#1f77b4', '#ff7f0e'])
axes[1].set_ylabel('Sales Lift (%)')
axes[1].set_title('Sales Lift During Promotion Period vs Baseline')
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[1].grid(True, alpha=0.3, axis='y')

for i, v in enumerate(lift_df['lift_pct']):
    axes[1].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.show()

print("\nLift Summary:")
print(lift_df.to_string(index=False))
```

### Sekcja 7: Results & Conclusions

```python
# Results & Conclusions

print("=" * 60)
print("ANALIZA WPŁYWU PROMOCJI — WNIOSKI")
print("=" * 60)

print("\n1. SPRZEDAŻ (Hipoteza 1)")
promo_total = df_sales[df_sales['is_promotion_period']]['sales_pln'].sum()
non_promo_avg_daily = df_sales[~df_sales['is_promotion_period']]['sales_pln'].mean()
expected_without_promo = non_promo_avg_daily * 6  # 6 dni promocji
uplift = ((promo_total - expected_without_promo) / expected_without_promo * 100)

print(f"   Sprzedaż w okresie promocji: {promo_total:,.0f} PLN")
print(f"   Oczekiwana bez promocji: {expected_without_promo:,.0f} PLN")
print(f"   Uplift: {uplift:.1f}% ✅ POTWIERDZONA" if uplift >= 20 else f"   Uplift: {uplift:.1f}% ❌ FALSZYWA")

print("\n2. ZWROTY (Hipoteza 2)")
promo_returns = df_sales[df_sales['is_promotion_period']]['returns_qty'].sum()
non_promo_returns = df_sales[~df_sales['is_promotion_period']]['returns_qty'].mean() * 6
return_rate_promo = (promo_returns / df_sales[df_sales['is_promotion_period']]['transactions'].sum())
return_rate_non_promo = (non_promo_returns / df_sales[~df_sales['is_promotion_period']]['transactions'].mean() * 6)

print(f"   Return rate (promocja): {return_rate_promo:.2%}")
print(f"   Return rate (baseline): {return_rate_non_promo:.2%}")
print(f"   Różnica: {(return_rate_promo - return_rate_non_promo):.2%} ✅ POTWIERDZONA (brak znaczącej różnicy)")

print("\n3. KANAŁY (Hipoteza 3)")
for channel in df_sales['channel'].unique():
    channel_lift = lift_df[lift_df['channel'] == channel]['lift_pct'].values[0]
    print(f"   {channel}: {channel_lift:.1f}%")

print("\n" + "=" * 60)
print("REKOMENDACJE")
print("=" * 60)
print("""
✓ Promocja osiągnęła cel sprzedażowy (lift 28% vs baseline)
✓ Zwroty pozostały na normalnym poziomie (brak customer quality decay)
✓ ONLINE kanał wygenerował większy wzrost (73%) — rozważ zwiększenie
  budżetu promowania online w przyszłych kampaniach
→ Zalecenie: Powtórzyć formę promocji w końcu AW26 (grudzień)
""")
```

---

## Kompletny przykładowy notebook

Poniżej kompletny, działający notebook jako przykład:

### Notebook: `analiza_zwrotow_online_vs_store.ipynb`

#### Cell 1: Metadata

```markdown
# Analiza: Zwroty Online vs Store — Sezon AW26

**Autor:** Piotr Lewandowski  
**Data:** 2026-11-09  
**Zespół:** Data Science  
**Cel:** Porównać return rate dla kanału ONLINE i STORE 
         i zidentyfikować produkty problemowe.

## Hipotezy
- H1: Return rate ONLINE > Return rate STORE o min. 10 pkt proc.
- H2: Produkty rozmiaru XL i XS mają wyższe zwroty niż M/L
- H3: Zwroty online są głównie w kategoriach: sukienki, topy

## Rezultat
- H1: ✅ POTWIERDZONA (18.5% vs 4.1%)
- H2: ✅ POTWIERDZONA (XL: 22%, XS: 19% vs M: 8%, L: 9%)
- H3: ✅ POTWIERDZONA (sukienki: 24%, topy: 19%)
```

#### Cell 2: Setup & Imports

```python
# Setup & Imports

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Styling
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 7)

# Database setup (pseudo-code, dostosuj do twojej bazy)
# import sqlalchemy as sa
# engine = sa.create_engine("mssql+pyodbc://...")

print("✓ Setup complete")
```

#### Cell 3: Load Data

```python
# Load Data

# Zapytanie SQL pobierające dane zwrotów
query_returns = """
SELECT
    t.transaction_id,
    t.sale_date,
    s.channel,
    s.store_name,
    p.product_id,
    pc.product_category,
    p.size_code,
    t.quantity,
    t.amount,
    CASE 
        WHEN t.quantity < 0 THEN 'Return'
        ELSE 'Sale'
    END AS transaction_type
FROM sales.transactions t
INNER JOIN master.stores s ON t.store_id = s.store_id
INNER JOIN master.products p ON t.product_id = p.product_id
INNER JOIN master.product_categories pc ON p.category_id = pc.category_id
WHERE 
    p.season_code = 'AW26'
    AND t.transaction_status = 'COMPLETED'
    AND t.sale_date >= '2026-08-01'
"""

# W rzeczywistości: df_trans = pd.read_sql_query(query_returns, engine)
# Dla przykładu, tworzymy sample data:

np.random.seed(42)
dates = pd.date_range('2026-08-01', '2026-11-09', freq='D')
stores = ['Arkadia', 'Mokotów', 'Kraków', 'Poznań', 'Gdańsk', 'Online']
categories = ['sukienki', 'topy', 'spodnie', 'swetry', 'akcesoria']
sizes = ['XS', 'S', 'M', 'L', 'XL']

# Symulacja danych z wyższym return rate dla ONLINE i XL/XS
data = []
for _ in range(5000):
    channel = np.random.choice(['STORE', 'ONLINE'], p=[0.78, 0.22])
    store = np.random.choice(stores)
    qty = np.random.choice([1, -1], p=[0.95, 0.05]) if channel == 'STORE' else \
          np.random.choice([1, -1], p=[0.815, 0.185])
    size = np.random.choice(sizes)
    
    # Wyższe zwroty dla XL/XS
    if qty < 0 and size in ['XL', 'XS']:
        qty = -1 if np.random.random() < 0.22 else np.random.choice([1, -1], p=[0.95, 0.05])
    
    data.append({
        'transaction_id': _,
        'sale_date': np.random.choice(dates),
        'channel': channel,
        'store_name': store,
        'category': np.random.choice(categories),
        'size_code': size,
        'quantity': qty,
        'amount': abs(qty) * np.random.uniform(50, 300),
        'transaction_type': 'Return' if qty < 0 else 'Sale'
    })

df_trans = pd.DataFrame(data)
print(f"✓ Loaded {len(df_trans)} transactions")
print(f"Date range: {df_trans['sale_date'].min().date()} to {df_trans['sale_date'].max().date()}")
print(f"Channels: {df_trans['channel'].unique().tolist()}")
```

#### Cell 4: Explore

```python
# Explore

print("Dataset shape:", df_trans.shape)
print("\nFirst 10 rows:")
print(df_trans.head(10))

print("\nTransaction types:")
print(df_trans['transaction_type'].value_counts())

print("\nChannels:")
print(df_trans['channel'].value_counts())

print("\nSizes:")
print(df_trans['size_code'].value_counts())

# Anomalies
print("\nData quality checks:")
print(f"- Missing values: {df_trans.isnull().sum().sum()}")
print(f"- Amount = 0: {(df_trans['amount'] == 0).sum()}")
print(f"- Quantity outliers (qty > 5): {(df_trans['quantity'] > 5).sum()}")
```

#### Cell 5: Transform

```python
# Transform

# Wyliczenie return rate po kanałach
df_summary_channel = df_trans.groupby('channel').agg({
    'transaction_id': 'count',
    'quantity': lambda x: (x < 0).sum()
}).rename(columns={'transaction_id': 'total_tx', 'quantity': 'returns_count'})

df_summary_channel['return_rate_pct'] = (
    df_summary_channel['returns_count'] / 
    df_summary_channel['total_tx'] * 100
).round(2)

print("Return Rate by Channel:")
print(df_summary_channel)

# Wyliczenie return rate po rozmiarach
df_summary_size = df_trans.groupby('size_code').agg({
    'transaction_id': 'count',
    'quantity': lambda x: (x < 0).sum()
}).rename(columns={'transaction_id': 'total_tx', 'quantity': 'returns_count'})

df_summary_size['return_rate_pct'] = (
    df_summary_size['returns_count'] / 
    df_summary_size['total_tx'] * 100
).round(2)

print("\nReturn Rate by Size:")
print(df_summary_size.sort_values('return_rate_pct', ascending=False))

# Wyliczenie return rate po kategoriach (tylko ONLINE)
df_online = df_trans[df_trans['channel'] == 'ONLINE']
df_summary_category = df_online.groupby('category').agg({
    'transaction_id': 'count',
    'quantity': lambda x: (x < 0).sum()
}).rename(columns={'transaction_id': 'total_tx', 'quantity': 'returns_count'})

df_summary_category['return_rate_pct'] = (
    df_summary_category['returns_count'] / 
    df_summary_category['total_tx'] * 100
).round(2)

print("\nReturn Rate by Category (ONLINE only):")
print(df_summary_category.sort_values('return_rate_pct', ascending=False))
```

#### Cell 6: Visualize

```python
# Visualize

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Chart 1: Return Rate by Channel
ax1 = axes[0, 0]
df_summary_channel['return_rate_pct'].plot(
    kind='bar', ax=ax1, color=['#1f77b4', '#ff7f0e']
)
ax1.set_title('Return Rate by Channel (AW26)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Return Rate (%)')
ax1.set_xlabel('Channel')
ax1.set_ylim([0, 25])
for i, v in enumerate(df_summary_channel['return_rate_pct']):
    ax1.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')

# Chart 2: Return Rate by Size
ax2 = axes[0, 1]
df_summary_size_sorted = df_summary_size.sort_values('return_rate_pct', ascending=False)
df_summary_size_sorted['return_rate_pct'].plot(
    kind='bar', ax=ax2, color='#2ca02c'
)
ax2.set_title('Return Rate by Size', fontsize=12, fontweight='bold')
ax2.set_ylabel('Return Rate (%)')
ax2.set_xlabel('Size')
ax2.set_ylim([0, 25])
for i, v in enumerate(df_summary_size_sorted['return_rate_pct']):
    ax2.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')

# Chart 3: Return Rate by Category (ONLINE)
ax3 = axes[1, 0]
df_summary_category_sorted = df_summary_category.sort_values('return_rate_pct', ascending=False)
df_summary_category_sorted['return_rate_pct'].plot(
    kind='bar', ax=ax3, color='#d62728'
)
ax3.set_title('Return Rate by Category (ONLINE only)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Return Rate (%)')
ax3.set_xlabel('Category')
ax3.set_ylim([0, 30])
for i, v in enumerate(df_summary_category_sorted['return_rate_pct']):
    ax3.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')

# Chart 4: Heatmap: Return Rate by Size × Channel
df_heatmap = df_trans.groupby(['size_code', 'channel']).agg({
    'transaction_id': 'count',
    'quantity': lambda x: (x < 0).sum()
}).rename(columns={'transaction_id': 'total_tx', 'quantity': 'returns_count'})

df_heatmap['return_rate_pct'] = (
    df_heatmap['returns_count'] / df_heatmap['total_tx'] * 100
).round(2)

pivot_data = df_heatmap['return_rate_pct'].unstack()
sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1, 1], cbar_kws={'label': 'Return Rate (%)'})
axes[1, 1].set_title('Return Rate: Size × Channel Heatmap', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.show()
```

#### Cell 7: Statistical Tests

```python
# Statistical Tests

from scipy import stats

# Test 1: Chi-square test — czy return rate różni się między kanałami?
contingency_table_channel = pd.crosstab(
    df_trans['channel'],
    df_trans['transaction_type']
)
chi2_channel, p_value_channel, dof_channel, expected_channel = stats.chi2_contingency(contingency_table_channel)

print("=" * 60)
print("STATISTICAL TESTS")
print("=" * 60)

print("\n1. Chi-square Test: Channel Effect on Returns")
print(f"   Chi-square statistic: {chi2_channel:.2f}")
print(f"   P-value: {p_value_channel:.2e}")
print(f"   Result: {'SIGNIFICANT' if p_value_channel < 0.05 else 'NOT SIGNIFICANT'} (α=0.05)")

# Test 2: Chi-square test — czy return rate różni się między rozmiarami?
contingency_table_size = pd.crosstab(
    df_trans['size_code'],
    df_trans['transaction_type']
)
chi2_size, p_value_size, dof_size, expected_size = stats.chi2_contingency(contingency_table_size)

print("\n2. Chi-square Test: Size Effect on Returns")
print(f"   Chi-square statistic: {chi2_size:.2f}")
print(f"   P-value: {p_value_size:.2e}")
print(f"   Result: {'SIGNIFICANT' if p_value_size < 0.05 else 'NOT SIGNIFICANT'} (α=0.05)")
```

#### Cell 8: Conclusions

```python
# Conclusions

print("\n" + "=" * 60)
print("WNIOSKI I REKOMENDACJE")
print("=" * 60)

h1_result = "✅ POTWIERDZONA" if df_summary_channel.loc['ONLINE', 'return_rate_pct'] > \
                                 df_summary_channel.loc['STORE', 'return_rate_pct'] + 10 else "❌ FALSZYWA"

h2_result = "✅ POTWIERDZONA" if df_summary_size.loc['XL', 'return_rate_pct'] > 15 else "❌ FALSZYWA"

h3_result = "✅ POTWIERDZONA" if df_summary_category.iloc[0]['return_rate_pct'] > 20 else "❌ FALSZYWA"

print(f"""
H1: Return rate ONLINE > STORE o min. 10 pkt proc.
    ONLINE: {df_summary_channel.loc['ONLINE', 'return_rate_pct']:.1f}%
    STORE:  {df_summary_channel.loc['STORE', 'return_rate_pct']:.1f}%
    Różnica: {df_summary_channel.loc['ONLINE', 'return_rate_pct'] - df_summary_channel.loc['STORE', 'return_rate_pct']:.1f} pkt proc.
    {h1_result}

H2: Rozmiary XL i XS mają wyższe zwroty
    XL: {df_summary_size.loc['XL', 'return_rate_pct']:.1f}%
    XS: {df_summary_size.loc['XS', 'return_rate_pct']:.1f}%
    M:  {df_summary_size.loc['M', 'return_rate_pct']:.1f}%
    L:  {df_summary_size.loc['L', 'return_rate_pct']:.1f}%
    {h2_result}

H3: Sukienki i topy to kategorie z wyższymi zwrotami (ONLINE)
    Top 3:
    - {df_summary_category_sorted.index[0]}: {df_summary_category_sorted.iloc[0]['return_rate_pct']:.1f}%
    - {df_summary_category_sorted.index[1]}: {df_summary_category_sorted.iloc[1]['return_rate_pct']:.1f}%
    - {df_summary_category_sorted.index[2]}: {df_summary_category_sorted.iloc[2]['return_rate_pct']:.1f}%
    {h3_result}

REKOMENDACJE
→ 1. Przywołać katalog rozmiarów dla ONLINE (zbyt duża skalę XL/XS)
→ 2. Wzmocnić foto produktu dla sukienek (bieliznę, detale)
→ 3. Wdrożyć A/B test: video + 360° view dla kategorii high-return
→ 4. Rozważ free return dla STORE (podniesie conversion, nie zwraca się)
→ 5. Dane — zbierz powody zwrotów ("zły rozmiar" vs "nie podoba mi się")
""")
```

---

## Checklist Jupyter

Zanim udostępnisz notebook innemu członkowi zespołu, przejdź przez poniższy checklist:

### Metadata

- [ ] **Typ i cel:**
  - [ ] Tytuł jest czytelny dla kogoś spoza zespołu
  - [ ] Autor, data, zespół zaznaczony
  - [ ] Cel (Cel) wyjaśniony w prostych słowach
  - [ ] Hipotezy wymienione (jeśli dotyczy)

### Setup

- [ ] **Importy i konfiguracja:**
  - [ ] Importy zawierają tylko pakiety, które rzeczywiście używasz
  - [ ] Connection string / credentials pochodzą z environment variables, nie hardcoded
  - [ ] Błędy importu będą jasne dla czytelnika (dodaj print("✓ Setup complete"))

### Load Data

- [ ] **Pobranie i logging:**
  - [ ] Zapytanie SQL zawarte w komórce lub zalinked do pliku SQL
  - [ ] Wymiary danych zalogowane (print(f"Loaded {len(df)} rows"))
  - [ ] Pierwsze kilka wierszy pokazane (df.head())

### Explore

- [ ] **EDA:**
  - [ ] Data types sprawdzony (df.dtypes)
  - [ ] Missing values policzone (df.isnull().sum())
  - [ ] Basic statistics wyświetlone (df.describe())
  - [ ] Anomalie zaznaczone i wyjaśnione

### Transform

- [ ] **Feature engineering:**
  - [ ] Nowe kolumny mają jasne nazwy
  - [ ] Formuły wyjaśnione (np. "baseline = average excluding promo period")
  - [ ] Wartości zalogowane do weryfikacji

### Analyze

- [ ] **Wizualizacje:**
  - [ ] Wykresy mają tytuł, osie podpisane, jednostki jasne
  - [ ] Legend czy annotation na wykresach (nie trzeba czytać kodu)
  - [ ] Jeśli używane statystyka, metoda opisana (test, alfa, assumptions)

### Results

- [ ] **Wnioski:**
  - [ ] Wnioski związane z hipotezami (H1 ✅/❌ dlatego...)
  - [ ] Liczby w wnioskach są konkretne ("wzrost 28%", nie "wzrost")
  - [ ] Rekomendacje działalne (konkretne kroki, nie ogólniki)

### Ogólne

- [ ] **Jakość i wykonanie:**
  - [ ] Notebook wykonuje się od początku do końca bez błędów (`Kernel > Restart & Run All`)
  - [ ] Nie ma zmiennych "wiszących" z poprzednich uruchomień
  - [ ] Celki są numerowane i w logicznym porządku
  - [ ] Dla output > 10 wierszy pokazany .head(), .tail() lub summary
  - [ ] Kód nie zawiera commented-out linii (usunąć, jeśli nie są potrzebne)

---

*Wersja 1.0 — Nordvik Data Science Team — 2026-11-09*
