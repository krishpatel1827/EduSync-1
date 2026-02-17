// 🧊 PREMIUM GLASSMORPHISM ALERTS
// Optimized for smooth animations and high-end feel

function createAlertElement(type, message, icon) {
    const alertDiv = document.createElement('div');
    
    // Base classes for premium glass look
    alertDiv.className = `glass-morphism position-fixed top-0 start-50 translate-middle-x mt-4 p-3 pe-5 rounded-4 shadow-lg`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '320px';
    alertDiv.style.maxWidth = '90%';
    alertDiv.style.opacity = '0';
    alertDiv.style.transform = 'translate(-50%, -20px)';
    alertDiv.style.transition = 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)';
    alertDiv.style.display = 'flex';
    alertDiv.style.alignItems = 'center';
    alertDiv.style.gap = '12px';
    
    // Context-based border/glow
    const colors = {
        success: { border: '#10B981', bg: 'rgba(16, 185, 129, 0.1)' },
        error: { border: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)' },
        warning: { border: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' },
        info: { border: '#3B82F6', bg: 'rgba(59, 130, 246, 0.1)' }
    };
    
    const config = colors[type] || colors.info;
    alertDiv.style.borderLeft = `4px solid ${config.border}`;
    
    alertDiv.innerHTML = `
        <div style="font-size: 1.5rem;">${icon}</div>
        <div style="flex: 1;">
            <div style="font-weight: 700; font-size: 0.95rem; color: var(--clr-text);">${type.toUpperCase()}</div>
            <div style="font-size: 0.85rem; color: var(--clr-text-muted);">${message}</div>
        </div>
        <button type="button" class="btn-close position-absolute top-50 end-0 translate-middle-y me-3" 
            onclick="this.parentElement.style.opacity='0'; this.parentElement.style.transform='translate(-50%, -20px)'; setTimeout(()=>this.parentElement.remove(), 500);" 
            aria-label="Close" style="font-size: 0.7rem;"></button>
    `;

    document.body.appendChild(alertDiv);

    // Trigger Entrance
    requestAnimationFrame(() => {
        alertDiv.style.opacity = '1';
        alertDiv.style.transform = 'translate(-50%, 0)';
    });

    // Auto Removal
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translate(-50%, -20px)';
            setTimeout(() => alertDiv.remove(), 500);
        }
    }, 5000);
}

function showSuccessAlert(message) {
    createAlertElement('success', message, '✅');
}

function showErrorAlert(message) {
    createAlertElement('error', message, '❌');
}

function showWarningAlert(message) {
    createAlertElement('warning', message, '⚠️');
}

function showInfoAlert(message) {
    createAlertElement('info', message, 'ℹ️');
}
