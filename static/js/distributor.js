// static/js/distributor.js
function setupDistributorDashboard() {
    // Confirmations
    document.querySelectorAll('form[action*="process_order"] button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!confirm('Process this order?')) e.preventDefault();
        });
    });

    // Real-time updates
    if (typeof EventSource !== 'undefined') {
        const eventSource = new EventSource('/order_updates');
        eventSource.onmessage = handleOrderUpdate;
    }
}

function handleOrderUpdate(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'order_update') {
        updateOrderRow(data.order_id, data.status);
    }
}

function updateOrderRow(orderId, status) {
    const row = document.querySelector(`tr[data-order-id="${orderId}"]`);
    if (!row) return;
    
    row.querySelector('.order-status').innerHTML = `
        <i class="bi ${getStatusIcon(status)}"></i> ${status}
    `;
    row.querySelector('.order-status').className = `order-status ${getStatusClass(status)}`;
}

// Helper functions
function getStatusIcon(status) {
    const icons = {
        'pending': 'hourglass',
        'processing': 'gear',
        'shipped': 'truck',
        'delivered': 'check-circle'
    };
    return `bi-${icons[status] || 'question-circle'}`;
}

function getStatusClass(status) {
    const classes = {
        'pending': 'text-warning',
        'processing': 'text-info',
        'shipped': 'text-success',
        'delivered': 'text-primary'
    };
    return classes[status] || '';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', setupDistributorDashboard);