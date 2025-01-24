-- Check LoanerCheckouts table structure
SELECT 
    c.name as column_name,
    t.name as data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('dbo.LoanerCheckouts')
ORDER BY c.column_id;

-- Check view definitions
SELECT 
    o.name as view_name,
    m.definition as view_definition
FROM sys.sql_modules m
JOIN sys.objects o ON m.object_id = o.object_id
WHERE o.type = 'V'
AND o.name IN ('AvailableLoaners', 'CheckedOutLoaners');
