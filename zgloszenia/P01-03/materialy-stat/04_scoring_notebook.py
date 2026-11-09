# Exported notebook cell; static text, not executed
legacy = read_sql('SELECT StyleCode, Signal FROM dbo.LegacyPriceSignal')
forecast = read_sql('SELECT ForecastWeek, StyleCode, StoreCode, Units FROM dbo.ForecastOutput')
# Scoring joins by StyleCode and WeekStart; training feature contract must be checked.
