-- Check for NULL or empty asset tags
SELECT COUNT(*) as null_count
FROM dbo.Formatted_Company_Inventory 
WHERE asset_tag IS NULL OR asset_tag = '';

-- Show records with NULL or empty asset tags
SELECT *
FROM dbo.Formatted_Company_Inventory 
WHERE asset_tag IS NULL OR asset_tag = '';

-- Check for duplicates
SELECT asset_tag, COUNT(*) as duplicate_count
FROM dbo.Formatted_Company_Inventory
WHERE asset_tag IS NOT NULL AND asset_tag != ''
GROUP BY asset_tag
HAVING COUNT(*) > 1;
