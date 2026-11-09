-- Static report consumer
CREATE VIEW reporting.vw_WeeklyPriceReview AS
SELECT f.ForecastWeek, f.StyleCode, f.StoreCode, l.Signal
FROM dbo.ForecastOutput f LEFT JOIN dbo.LegacyPriceSignal l ON l.StyleCode=f.StyleCode;
