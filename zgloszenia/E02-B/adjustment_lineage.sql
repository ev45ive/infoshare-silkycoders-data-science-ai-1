-- Adjustment ETL excerpt, release REL-2026.10.3
INSERT stg.Adjustment(AdjustmentId,StoreCode,AdjustedAt,AdjustmentType,AdjustmentAmount,ApprovalStatus,SourceFile,ExtractedAt)
SELECT AdjustmentId,StoreCode,TRY_CONVERT(date,AdjustedAt),AdjustmentType,TRY_CONVERT(decimal(12,2),AdjustmentAmount),ApprovalStatus,SourceFile,ExtractedAt
FROM src.AdjustmentRaw;
INSERT dbo.FactAdjustment(DateKey,StoreKey,AdjustmentId,AdjustmentTypeKey,AdjustmentAmount,ApprovalStatus)
SELECT d.DateKey,st.StoreKey,a.AdjustmentId,t.AdjustmentTypeKey,a.AdjustmentAmount,a.ApprovalStatus
FROM stg.Adjustment a JOIN dbo.DimDate d ON d.FullDate=a.AdjustedAt
JOIN dbo.DimStore st ON st.StoreCode=a.StoreCode
JOIN dbo.DimAdjustmentType t ON t.Label=a.AdjustmentType;
-- SourceFile/ExtractedAt are not copied to FactAdjustment.
