-- Add the foreign key constraint to ensure data integrity
ALTER TABLE dbo.Formatted_Company_Inventory 
ADD CONSTRAINT FK_Inventory_Location 
FOREIGN KEY (location_id) REFERENCES dbo.Locations(location_id);

-- Verify the constraint was added
SELECT 
    fk.name as constraint_name,
    OBJECT_NAME(fk.parent_object_id) as table_name,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) as column_name,
    OBJECT_NAME(fk.referenced_object_id) as referenced_table_name,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) as referenced_column_name
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE fk.name = 'FK_Inventory_Location';
