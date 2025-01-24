-- Let's see what our Locations population query actually did
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
FROM dbo.Formatted_Company_Inventory
WHERE site_name IS NOT NULL 
   OR room_number IS NOT NULL 
   OR room_name IS NOT NULL;

-- Let's try repopulating the Locations table
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

-- Now try updating location_ids again
UPDATE i
SET i.location_id = l.location_id
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON 
    COALESCE(i.site_name, 'Unknown') = l.site_name AND
    COALESCE(i.room_number, 'Unknown') = l.room_number;

-- Check results
SELECT COUNT(*) as total_records,
       COUNT(location_id) as records_with_location_id,
       COUNT(CASE WHEN location_id IS NULL THEN 1 END) as records_missing_location_id
FROM dbo.Formatted_Company_Inventory;
