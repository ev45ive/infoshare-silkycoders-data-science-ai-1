-- Static excerpt: proposed change analysis only
INSERT INTO dbo.ForecastOutput (ForecastWeek, StyleCode, StoreCode, Units)
SELECT WeekStart, StyleCode, StoreCode, PredictedUnits FROM stage.Forecast;
SELECT StyleCode, Signal FROM dbo.LegacyPriceSignal; -- downstream staging consumer
