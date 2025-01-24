-- Check if is_loaner flag exists
SELECT 
    c.name as column_name,
    t.name as data_type,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
AND c.name = 'is_loaner';

-- Test the views with sample data
SELECT TOP 5 * FROM dbo.AvailableLoaners;
SELECT TOP 5 * FROM dbo.CheckedOutLoaners;

-- Show table relationships
SELECT 
    fk.name AS ForeignKeyName,
    OBJECT_NAME(fk.parent_object_id) AS TableName,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ColumnName,
    OBJECT_NAME(fk.referenced_object_id) AS ReferencedTableName,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ReferencedColumnName
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'LoanerCheckouts'
   OR OBJECT_NAME(fk.referenced_object_id) = 'LoanerCheckouts';
