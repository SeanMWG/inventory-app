// Show details modal
function showDetails(item) {
    currentItem = item;
    
    // Update details view
    document.getElementById('detailSiteName').textContent = item.site_name || '';
    document.getElementById('detailRoomNumber').textContent = item.room_number || '';
    document.getElementById('detailRoomName').textContent = item.room_name || '';
    document.getElementById('detailAssetTag').textContent = item.asset_tag || '';
    document.getElementById('detailAssetType').textContent = item.asset_type || '';
    document.getElementById('detailModel').textContent = item.model || '';
    document.getElementById('detailSerialNumber').textContent = item.serial_number || '';
    document.getElementById('detailNotes').textContent = item.notes || '';
    document.getElementById('detailAssignedTo').textContent = item.assigned_to || '';
    document.getElementById('detailDateAssigned').textContent = item.date_assigned ? new Date(item.date_assigned).toLocaleDateString() : '';
    document.getElementById('detailDateDecommissioned').textContent = item.date_decommissioned ? new Date(item.date_decommissioned).toLocaleDateString() : '';
    
    // Show the details modal
    document.getElementById('detailsModal').style.display = 'block';
    
    // Set up audit button click handler
    document.getElementById('viewAuditButton').onclick = () => loadAuditLog(item.asset_tag);
    
    // Set up edit button click handler
    document.getElementById('detailsEditButton').onclick = () => editHardware(item);
}

// Edit hardware
function editHardware(item) {
    // Close details modal if it's open
    document.getElementById('detailsModal').style.display = 'none';
    
    // Update form with current values
    document.getElementById('siteName').value = item.site_name || '';
    document.getElementById('roomNumber').value = item.room_number || '';
    document.getElementById('roomName').value = item.room_name || '';
    document.getElementById('assetTag').value = item.asset_tag || '';
    document.getElementById('assetType').value = item.asset_type || '';
    document.getElementById('model').value = item.model || '';
    document.getElementById('serialNumber').value = item.serial_number || '';
    document.getElementById('notes').value = item.notes || '';
    document.getElementById('assignedTo').value = item.assigned_to || '';
    document.getElementById('dateAssigned').value = item.date_assigned ? item.date_assigned.split('T')[0] : '';
    document.getElementById('dateDecommissioned').value = item.date_decommissioned ? item.date_decommissioned.split('T')[0] : '';
    
    // Update modal title and button text
    document.getElementById('modalTitle').textContent = 'Edit Hardware';
    document.getElementById('submitButton').textContent = 'Update Hardware';
    
    // Show the form modal
    document.getElementById('formModal').style.display = 'block';
}

// Load audit log
async function loadAuditLog(assetTag) {
    try {
        const response = await fetch(`/api/audit/${assetTag}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const auditEntries = await response.json();
        
        // Clear existing entries
        const tbody = document.getElementById('auditTableBody');
        tbody.innerHTML = '';
        
        // Add new entries
        auditEntries.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(entry.changed_at).toLocaleString()}</td>
                <td>${entry.action_type}</td>
                <td>${entry.field_name}</td>
                <td>${entry.old_value || ''}</td>
                <td>${entry.new_value || ''}</td>
                <td>${entry.changed_by}</td>
            `;
            tbody.appendChild(row);
        });
        
        // Show the audit modal
        document.getElementById('auditModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading audit log:', error);
        alert('Error loading audit log');
    }
}
