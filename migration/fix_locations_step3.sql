-- First drop the foreign key so we can modify the Locations table
ALTER TABLE dbo.Formatted_Company_Inventory
DROP CONSTRAINT FK_Inventory_Location;

-- Clear out location_ids
UPDATE dbo.Formatted_Company_Inventory
SET location_id = NULL;

-- Now truncate and repopulate Locations
TRUNCATE TABLE dbo.Locations;

INSERT INTO dbo.Locations (site_name, room_number, room_name, room_type)
SELECT DISTINCT 
    ISNULL(site_name, N'Unknown') as site_name,
    ISNULL(room_number, N'Unknown') as room_number,
    ISNULL(room_name, N'Unknown') as room_name,
    CASE 
        WHEN room_name LIKE N'%Cubicle%' THEN N'Cubicle'
        WHEN room_name LIKE N'%Office%' THEN N'Office'
        WHEN room_name LIKE N'%Storage%' THEN N'Storage'
        WHEN room_name LIKE N'%Server%' THEN N'Server Room'
        ELSE N'Other'
    END as room_type
FROM dbo.Formatted_Company_Inventory;

-- Update location_ids
UPDATE i
SET i.location_id = l.location_id
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON 
    COALESCE(i.site_name, 'Unknown') = l.site_name AND
    COALESCE(i.room_number, 'Unknown') = l.room_number;

-- Add the foreign key back
ALTER TABLE dbo.Formatted_Company_Inventory 
ADD CONSTRAINT FK_Inventory_Location 
FOREIGN KEY (location_id) REFERENCES dbo.Locations(location_id);

-- Check results
SELECT COUNT(*) as total_records,
       COUNT(location_id) as records_with_location_id,
       COUNT(CASE WHEN location_id IS NULL THEN 1 END) as records_missing_location_id
FROM dbo.Formatted_Company_Inventory;
