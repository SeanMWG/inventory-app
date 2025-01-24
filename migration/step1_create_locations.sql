-- First, let's create a backup of the inventory table just in case
SELECT * INTO Formatted_Company_Inventory_Backup_20250124 FROM dbo.Formatted_Company_Inventory;

-- Then create the new Locations table
CREATE TABLE dbo.Locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    CONSTRAINT UQ_Location UNIQUE (site_name, room_number)
);

-- Let's verify the table was created correctly
SELECT * FROM sys.tables WHERE name = 'Locations';
SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Locations');
