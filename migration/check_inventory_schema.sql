-- Check the inventory table schema
SELECT 
    c.name as column_name,
    t.name as data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
ORDER BY c.column_id;

-- Check primary key info
SELECT 
    i.name as index_name,
    c.name as column_name,
    i.is_primary_key
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
AND i.is_primary_key = 1;
