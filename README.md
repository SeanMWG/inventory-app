# IT Hardware Inventory App

## Features
- Track hardware inventory
- Add items individually or import from Excel
- Sort by any column
- Search functionality
- Dark/Light mode
- Azure AD authentication

## Excel Import Format
To import data from Excel, create a spreadsheet with these columns:

### Required Columns
- manufacturer
- model_number
- hardware_type
- serial_number

### Optional Columns
- assigned_to
- location
- date_assigned (format: YYYY-MM-DD)
- date_decommissioned (format: YYYY-MM-DD)

### Example Excel Row
```
manufacturer: Dell
model_number: Latitude 5420
hardware_type: Laptop
serial_number: ABC123
assigned_to: John Doe
location: Main Office
date_assigned: 2024-01-14
date_decommissioned: [leave blank if not decommissioned]
```

## Development Setup
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run locally:
```bash
python app.py
```

## Azure Deployment
1. Push changes to GitHub:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

2. GitHub Actions will automatically deploy to Azure.

## Authentication
The application uses Azure AD (Entra ID) for authentication. Users must sign in with their Microsoft credentials to access the inventory system.
