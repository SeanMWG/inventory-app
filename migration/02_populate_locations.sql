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
