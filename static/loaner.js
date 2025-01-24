// Load available loaners
async function loadAvailableLoaners() {
    try {
        const response = await fetch('/api/loaners/available');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const items = await response.json();
        
        const tbody = document.querySelector('#available-items tbody');
        tbody.innerHTML = items.map(item => `
            <tr>
                <td>${item.asset_tag || ''}</td>
                <td>${item.asset_type || ''}</td>
                <td>${item.model || ''}</td>
                <td>${item.site_name} - ${item.room_number}</td>
                <td>
                    <button class="action-button" onclick="showCheckoutModal(${item.inventory_id}, '${item.asset_tag}')">
                        Check Out
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading available loaners:', error);
        alert('Error loading available loaners');
    }
}

// Load checked out items
async function loadCheckedOutItems() {
    try {
        const response = await fetch('/api/loaners/checked-out');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const items = await response.json();
        
        const tbody = document.querySelector('#checked-out-items tbody');
        tbody.innerHTML = items.map(item => `
            <tr>
                <td>${item.asset_tag || ''}</td>
                <td>${item.asset_type || ''}</td>
                <td>${item.model || ''}</td>
                <td>${item.user_name || ''}</td>
                <td>${item.checkout_date ? new Date(item.checkout_date).toLocaleDateString() : ''}</td>
                <td>${item.expected_return_date ? new Date(item.expected_return_date).toLocaleDateString() : 'N/A'}</td>
                <td>
                    <button class="action-button" onclick="showCheckinModal(
                        ${item.checkout_id},
                        '${item.asset_tag}',
                        '${item.user_name}',
                        '${item.checkout_date}'
                    )">
                        Check In
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading checked out items:', error);
        alert('Error loading checked out items');
    }
}

// Show checkout modal
function showCheckoutModal(inventoryId, assetTag) {
    document.getElementById('checkout-inventory-id').value = inventoryId;
    document.getElementById('checkout-asset-tag').textContent = assetTag;
    document.getElementById('checkout-user').value = '';
    document.getElementById('checkout-expected-return').value = '';
    document.getElementById('checkout-notes').value = '';
    document.getElementById('checkout-modal').style.display = 'block';
}

// Show checkin modal
function showCheckinModal(checkoutId, assetTag, userName, checkoutDate) {
    document.getElementById('checkin-checkout-id').value = checkoutId;
    document.getElementById('checkin-asset-tag').textContent = assetTag;
    document.getElementById('checkin-user').textContent = userName;
    document.getElementById('checkin-date').textContent = new Date(checkoutDate).toLocaleDateString();
    document.getElementById('checkin-modal').style.display = 'block';
}

// Close modals
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadAvailableLoaners();
    loadCheckedOutItems();
    
    // Set up tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('onclick').match(/'([^']+)'/)[1];
            showTab(tabName);
        });
    });
    
    // Set up form submissions
    document.getElementById('checkout-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/loaners/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    inventory_id: document.getElementById('checkout-inventory-id').value,
                    user_name: document.getElementById('checkout-user').value,
                    expected_return_date: document.getElementById('checkout-expected-return').value,
                    notes: document.getElementById('checkout-notes').value
                })
            });
            
            if (!response.ok) throw new Error('Checkout failed');
            
            closeModal('checkout-modal');
            loadAvailableLoaners();
            loadCheckedOutItems();
            alert('Item checked out successfully');
        } catch (error) {
            console.error('Error during checkout:', error);
            alert('Failed to check out item');
        }
    });
    
    document.getElementById('checkin-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/loaners/checkin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    checkout_id: document.getElementById('checkin-checkout-id').value
                })
            });
            
            if (!response.ok) throw new Error('Check-in failed');
            
            closeModal('checkin-modal');
            loadAvailableLoaners();
            loadCheckedOutItems();
            alert('Item checked in successfully');
        } catch (error) {
            console.error('Error during check-in:', error);
            alert('Failed to check in item');
        }
    });
    
    // Set up modal close buttons
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.onclick = function() {
            this.closest('.modal').style.display = 'none';
        };
    });
    
    // Close modals when clicking outside
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
});
