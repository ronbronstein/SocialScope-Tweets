// Main JavaScript for SocialScope-Tweets Web UI

document.addEventListener('DOMContentLoaded', function() {
    initDateValidation();
    initFormValidation();
    initCodeBlocks();
    initBackToTop();
    initDarkMode();
    initLoadingState();
});

/**
 * Initialize date validation for the date range inputs
 */
function initDateValidation() {
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
}

/**
 * Initialize form validation for analysis form
 */
function initFormValidation() {
    const analysisForm = document.querySelector('form[action*="analyze"]');
    
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(event) {
            if (!validateAnalysisForm()) {
                event.preventDefault();
            }
        });
    }
}

/**
 * Validate analysis form fields
 */
function validateAnalysisForm() {
    const usernameInput = document.getElementById('username');
    
    if (!usernameInput) return true;
    
    const username = usernameInput.value.trim();
    
    if (!username) {
        showValidationError(usernameInput, 'Please enter a Twitter username');
        return false;
    }
    
    // Clear any previous errors
    if (usernameInput.classList.contains('is-invalid')) {
        usernameInput.classList.remove('is-invalid');
        const errorDiv = usernameInput.parentElement.querySelector('.invalid-feedback');
        if (errorDiv) errorDiv.remove();
    }
    
    return true;
}

/**
 * Show validation error for a form field
 */
function showValidationError(inputElement, message) {
    // Create or update error message
    let errorDiv = inputElement.parentElement.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        inputElement.parentElement.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
    inputElement.classList.add('is-invalid');
}

/**
 * Add copy to clipboard functionality for code blocks
 */
function initCodeBlocks() {
    document.querySelectorAll('pre').forEach(block => {
        // Skip if already initialized
        if (block.querySelector('.btn-copy')) return;
        
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2 btn-copy';
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
}

/**
 * Initialize back to top button functionality
 */
function initBackToTop() {
    const backToTopButton = document.getElementById('backToTop');
    
    if (backToTopButton) {
        // Show/hide button based on scroll position
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopButton.style.display = 'block';
            } else {
                backToTopButton.style.display = 'none';
            }
        });
        
        // Scroll to top when clicked
        backToTopButton.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

/**
 * Initialize dark mode toggle functionality
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkModeToggle) {
        // Check if user previously enabled dark mode
        if (localStorage.getItem('darkMode') === 'enabled') {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
        
        // Add event listener
        darkModeToggle.addEventListener('change', toggleDarkMode);
    }
}

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    
    // Save preference
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
}

/**
 * Initialize loading state for form submissions
 */
function initLoadingState() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                enableLoadingState(submitButton);
            }
        });
    });
}

/**
 * Enable loading state on a button
 */
function enableLoadingState(button) {
    const originalText = button.innerHTML;
    button.setAttribute('data-original-text', originalText);
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    button.disabled = true;
}

/**
 * Disable loading state on a button
 */
function disableLoadingState(button) {
    const originalText = button.getAttribute('data-original-text');
    button.innerHTML = originalText;
    button.disabled = false;
}