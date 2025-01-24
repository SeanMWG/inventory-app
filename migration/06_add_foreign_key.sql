IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys 
    WHERE name = 'FK_Inventory_Location'
)
BEGIN
    ALTER TABLE dbo.Formatted_Company_Inventory 
    ADD CONSTRAINT FK_Inventory_Location 
    FOREIGN KEY (location_id) REFERENCES dbo.Locations(location_id);
END;
