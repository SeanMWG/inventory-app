-- Check for any foreign keys referencing Formatted_Company_Inventory
SELECT 
    fk.name AS ForeignKeyName,
    OBJECT_NAME(fk.parent_object_id) AS TableName,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ColumnName,
    OBJECT_NAME(fk.referenced_object_id) AS ReferencedTableName,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ReferencedColumnName
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.referenced_object_id) = 'Formatted_Company_Inventory'
   OR OBJECT_NAME(fk.parent_object_id) = 'Formatted_Company_Inventory';

-- Check for any indexes on Formatted_Company_Inventory
SELECT 
    i.name AS IndexName,
    i.type_desc AS IndexType,
    i.is_primary_key,
    i.is_unique,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS IndexColumns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
GROUP BY i.name, i.type_desc, i.is_primary_key, i.is_unique;
