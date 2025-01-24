-- First, let's see what distinct locations we have
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
   OR room_name IS NOT NULL
ORDER BY site_name, room_number;

-- If the above looks good, run this to populate the Locations table
INSERT INTO dbo.Locations (site_name, room_number, room_name, room_type)
SELECT DISTINCT 
    ISNULL(site_name, N'Unknown'),
    ISNULL(room_number, N'Unknown'),
    ISNULL(room_name, N'Unknown'),
    CASE 
        WHEN room_name LIKE N'%Cubicle%' THEN N'Cubicle'
        WHEN room_name LIKE N'%Office%' THEN N'Office'
        WHEN room_name LIKE N'%Storage%' THEN N'Storage'
        WHEN room_name LIKE N'%Server%' THEN N'Server Room'
        ELSE N'Other'
    END
FROM dbo.Formatted_Company_Inventory
WHERE site_name IS NOT NULL 
   OR room_number IS NOT NULL 
   OR room_name IS NOT NULL;

-- Verify the data was inserted correctly
SELECT * FROM dbo.Locations ORDER BY site_name, room_number;
