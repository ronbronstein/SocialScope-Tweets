// Main JavaScript for SocialScope-Tweets Web UI

document.addEventListener('DOMContentLoaded', function() {
    // Handle date range validation
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        // Ensure end date is not before start date
        endDateInput.addEventListener('change', function() {
            if (startDateInput.value && endDateInput.value) {
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                
                if (endDate < startDate) {
                    alert('End date cannot be before start date.');
                    endDateInput.value = '';
                }
            }
        });
        
        // Ensure start date is not after end date
        startDateInput.addEventListener('change', function() {
            if (startDateInput.value && endDateInput.value) {
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                
                if (startDate > endDate) {
                    alert('Start date cannot be after end date.');
                    startDateInput.value = '';
                }
            }
        });
        
        // Prevent future dates
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayISOString = today.toISOString().split('T')[0];
        
        startDateInput.setAttribute('max', todayISOString);
        endDateInput.setAttribute('max', todayISOString);
    }
    
    // Add 'copy to clipboard' functionality for code blocks
    document.querySelectorAll('pre').forEach(block => {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
        button.innerHTML = '<i class="fas fa-copy"></i>';
        button.title = 'Copy to clipboard';
        
        button.addEventListener('click', () => {
            const textToCopy = block.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {
                button.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
        });
        
        // Only add the button if the pre has a parent with position relative
        const parent = block.parentElement;
        if (parent) {
            const parentStyle = window.getComputedStyle(parent);
            if (parentStyle.position !== 'relative') {
                parent.style.position = 'relative';
            }
            parent.appendChild(button);
        }
    });
});