-- Step 1: Add the location_id column to the inventory table
-- Run this statement first:
ALTER TABLE dbo.Formatted_Company_Inventory ADD
    location_id INT NULL;
GO

-- Step 2: Create an index for better performance
-- Run this statement second (after the column is added):
CREATE INDEX IX_Inventory_LocationId ON dbo.Formatted_Company_Inventory(location_id);
GO

-- Step 3: Update the location_id values
-- Run this statement third:
UPDATE i
SET i.location_id = l.location_id
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON 
    ISNULL(i.site_name, N'Unknown') = l.site_name AND
    ISNULL(i.room_number, N'Unknown') = l.room_number;
GO

-- Step 4: Verify the updates worked correctly
-- Run this statement last:
SELECT TOP 100 
    i.site_name,
    i.room_number,
    i.room_name,
    l.location_id,
    l.room_type
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON i.location_id = l.location_id
ORDER BY l.site_name, l.room_number;
