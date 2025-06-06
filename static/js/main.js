// Notification system
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPhoneNumber(phone) {
    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');
    
    // Format as +7 (XXX) XXX-XX-XX
    if (cleaned.length === 11 && cleaned.startsWith('7')) {
        return `+7 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7, 9)}-${cleaned.slice(9)}`;
    } else if (cleaned.length === 10) {
        return `+7 (${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 8)}-${cleaned.slice(8)}`;
    }
    
    return phone;
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 11;
}

// Geolocation utilities
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Геолокация не поддерживается этим браузером'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => resolve(position),
            error => {
                let message = 'Не удалось получить местоположение';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'Доступ к геолокации запрещен';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Информация о местоположении недоступна';
                        break;
                    case error.TIMEOUT:
                        message = 'Время ожидания получения местоположения истекло';
                        break;
                }
                reject(new Error(message));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000 // 5 minutes
            }
        );
    });
}

// Distance calculation
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// API helpers
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return null;
    }
}

// Form helpers
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}

function resetForm(form) {
    form.reset();
    // Clear any custom validation messages
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.classList.remove('error', 'success');
    });
}

// Input validation styling
function setInputError(input, message) {
    input.classList.add('error');
    input.classList.remove('success');
    
    // Remove existing error message
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    if (message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.color = '#dc3545';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        input.parentNode.appendChild(errorDiv);
    }
}

function setInputSuccess(input) {
    input.classList.add('success');
    input.classList.remove('error');
    
    // Remove error message
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

// Real-time form validation
function setupFormValidation(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(this);
        });
        
        input.addEventListener('input', function() {
            // Clear error state on input
            if (this.classList.contains('error')) {
                this.classList.remove('error');
                const errorMessage = this.parentNode.querySelector('.error-message');
                if (errorMessage) {
                    errorMessage.remove();
                }
            }
        });
    });
}

function validateInput(input) {
    const value = input.value.trim();
    const type = input.type;
    const name = input.name;
    
    if (input.required && !value) {
        setInputError(input, 'Это поле обязательно');
        return false;
    }
    
    if (type === 'email' && value && !validateEmail(value)) {
        setInputError(input, 'Введите корректный email');
        return false;
    }
    
    if (type === 'tel' && value && !validatePhone(value)) {
        setInputError(input, 'Введите корректный номер телефона');
        return false;
    }
    
    if (name === 'password' && value && value.length < 6) {
        setInputError(input, 'Пароль должен содержать минимум 6 символов');
        return false;
    }
    
    if (type === 'number' && value) {
        const num = parseFloat(value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);
        
        if (isNaN(num)) {
            setInputError(input, 'Введите корректное число');
            return false;
        }
        
        if (!isNaN(min) && num < min) {
            setInputError(input, `Значение должно быть не менее ${min}`);
            return false;
        }
        
        if (!isNaN(max) && num > max) {
            setInputError(input, `Значение должно быть не более ${max}`);
            return false;
        }
    }
    
    setInputSuccess(input);
    return true;
}

// Initialize form validation on page load
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        setupFormValidation(form);
    });
});

// Loading state management
function setLoadingState(element, loading = true) {
    if (loading) {
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
    } else {
        element.disabled = false;
        element.textContent = element.dataset.originalText || element.textContent;
    }
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Auto-refresh functionality
class AutoRefresh {
    constructor(callback, interval = 30000) {
        this.callback = callback;
        this.interval = interval;
        this.timer = null;
        this.isActive = false;
    }
    
    start() {
        if (!this.isActive) {
            this.isActive = true;
            this.timer = setInterval(this.callback, this.interval);
        }
    }
    
    stop() {
        if (this.isActive) {
            this.isActive = false;
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    restart() {
        this.stop();
        this.start();
    }
}

// Page visibility API for pausing auto-refresh when tab is not visible
document.addEventListener('visibilitychange', function() {
    if (window.autoRefresh) {
        if (document.hidden) {
            window.autoRefresh.stop();
        } else {
            window.autoRefresh.start();
        }
    }
});

// Error handling for images
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.src = '/static/images/placeholder.png'; // Fallback image
            this.alt = 'Изображение недоступно';
        });
    });
});

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal[style*="block"]');
        openModals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    // Ctrl+Enter to submit forms
    if (e.ctrlKey && e.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.form) {
            const submitButton = activeElement.form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
    }
});

// Print functionality
function printReceipt() {
    const receiptContent = document.getElementById('receiptDetails').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Чек на поездку</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .receipt { border: 1px solid #ccc; padding: 20px; }
                    h2 { color: #333; }
                    p { margin: 10px 0; }
                </style>
            </head>
            <body>
                ${receiptContent}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Export functions for global use
window.showNotification = showNotification;
window.getCurrentPosition = getCurrentPosition;
window.calculateDistance = calculateDistance;
window.apiRequest = apiRequest;
window.AutoRefresh = AutoRefresh;
window.printReceipt = printReceipt;