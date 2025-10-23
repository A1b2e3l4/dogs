class WoofcarePayments {
    constructor() {
        this.intasendPublicKey = "ISPubKey_test_"; // Replace with your actual public key
        this.apiBaseUrl = "https://payment.intasend.com/api/v1/payment";
        this.init();
    }

    init() {
        this.setupPaymentListeners();
        this.setupMpesaNumberValidation();
    }

    setupPaymentListeners() {
        const paymentForm = document.getElementById('payment-form');
        if (paymentForm) {
            paymentForm.addEventListener('submit', (e) => this.handlePayment(e));
        }

        // Listen for payment status updates
        this.pollPaymentStatus();
    }

    setupMpesaNumberValidation() {
        const mpesaInput = document.getElementById('mpesa_number');
        if (mpesaInput) {
            mpesaInput.addEventListener('input', (e) => {
                this.validateMpesaNumber(e.target);
            });
        }
    }

    validateMpesaNumber(input) {
        let value = input.value.replace(/\D/g, ''); // Remove non-digits
        
        // Format as Kenyan number
        if (value.startsWith('0')) {
            value = '254' + value.substring(1);
        } else if (value.startsWith('7') || value.startsWith('1')) {
            value = '254' + value;
        }
        
        input.value = value;
        
        // Validate length
        if (value.length === 12 && value.startsWith('254')) {
            input.style.borderColor = 'var(--success-color)';
            return true;
        } else {
            input.style.borderColor = 'var(--error-color)';
            return false;
        }
    }

    async handlePayment(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const mpesaNumber = document.getElementById('mpesa_number').value;
        
        // Validate M-Pesa number
        if (!this.validateMpesaNumber({ value: mpesaNumber })) {
            this.showMessage('Please enter a valid Kenyan phone number (e.g., 254712345678)', 'error');
            return;
        }

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        try {
            const response = await this.initiateMpesaPayment(form);
            
            if (response.success) {
                this.showMessage('Payment initiated! Check your phone to complete the payment.', 'success');
                this.startPaymentPolling(response.invoice_id);
            } else {
                throw new Error(response.message || 'Payment initiation failed');
            }
        } catch (error) {
            console.error('Payment error:', error);
            this.showMessage('Payment failed: ' + error.message, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Pay with M-Pesa';
        }
    }

    async initiateMpesaPayment(form) {
        const formData = new FormData(form);
        const payload = {
            public_key: this.intasendPublicKey,
            amount: parseFloat(formData.get('amount')),
            currency: "KES",
            phone_number: formData.get('mpesa_number'),
            email: formData.get('email') || '',
            first_name: formData.get('first_name') || '',
            last_name: formData.get('last_name') || '',
            order_id: formData.get('order_id') || this.generateOrderId()
        };

        // Show loading state
        this.showLoadingState(true);

        const response = await fetch('/checkout/' + formData.get('dog_id'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Network error');
        }

        return data;
    }

    async startPaymentPolling(invoiceId) {
        let attempts = 0;
        const maxAttempts = 30; // 5 minutes at 10-second intervals
        
        const poll = setInterval(async () => {
            attempts++;
            
            try {
                const status = await this.checkPaymentStatus(invoiceId);
                
                if (status.state === 'COMPLETED') {
                    clearInterval(poll);
                    this.handleSuccessfulPayment(invoiceId);
                } else if (status.state === 'FAILED' || status.state === 'DECLINED') {
                    clearInterval(poll);
                    this.handleFailedPayment(status);
                } else if (attempts >= maxAttempts) {
                    clearInterval(poll);
                    this.handleTimeout();
                }
            } catch (error) {
                console.error('Polling error:', error);
                if (attempts >= maxAttempts) {
                    clearInterval(poll);
                    this.handleTimeout();
                }
            }
        }, 10000); // Check every 10 seconds
    }

    async checkPaymentStatus(invoiceId) {
        const response = await fetch(`/api/payment/status/${invoiceId}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to check payment status');
        }

        return await response.json();
    }

    handleSuccessfulPayment(invoiceId) {
        this.showMessage('Payment completed successfully!', 'success');
        
        // Redirect to order confirmation
        setTimeout(() => {
            window.location.href = `/order-confirmation/${invoiceId}`;
        }, 2000);
    }

    handleFailedPayment(status) {
        this.showMessage(`Payment failed: ${status.reason || 'Please try again'}`, 'error');
        this.resetPaymentForm();
    }

    handleTimeout() {
        this.showMessage('Payment timeout. Please check your phone or try again.', 'error');
        this.resetPaymentForm();
    }

    resetPaymentForm() {
        const submitBtn = document.querySelector('#payment-form button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Pay with M-Pesa';
        }
        this.showLoadingState(false);
    }

    showLoadingState(show) {
        const loadingElement = document.getElementById('payment-loading') || this.createLoadingElement();
        
        if (show) {
            loadingElement.style.display = 'block';
        } else {
            loadingElement.style.display = 'none';
        }
    }

    createLoadingElement() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'payment-loading';
        loadingDiv.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="border: 4px solid #f3f3f3; border-top: 4px solid var(--primary-color); border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto;"></div>
                <p style="margin-top: 10px;">Processing payment...</p>
            </div>
        `;
        loadingDiv.style.display = 'none';
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        const paymentForm = document.getElementById('payment-form');
        if (paymentForm) {
            paymentForm.appendChild(loadingDiv);
        }
        
        return loadingDiv;
    }

    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.payment-message');
        existingMessages.forEach(msg => msg.remove());
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `payment-message flash ${type}`;
        messageDiv.textContent = message;
        messageDiv.style.margin = '10px 0';
        
        const paymentForm = document.getElementById('payment-form');
        if (paymentForm) {
            paymentForm.insertBefore(messageDiv, paymentForm.firstChild);
        } else {
            // Fallback to body
            document.body.insertBefore(messageDiv, document.body.firstChild);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    generateOrderId() {
        return 'WOOF_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Utility function to format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: 'KES'
        }).format(amount);
    }

    // Handle payment callbacks from IntaSend
    handlePaymentCallback(data) {
        if (data && data.invoice_id) {
            this.startPaymentPolling(data.invoice_id);
        }
    }
}

// Initialize payments when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.woofcarePayments = new WoofcarePayments();
    
    // Add custom styles for payment form
    const style = document.createElement('style');
    style.textContent = `
        .payment-info {
            background: var(--secondary-color);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        .payment-summary {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .summary-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .total-amount {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
            text-align: center;
            margin: 1rem 0;
        }
        
        .mpesa-note {
            background: #e8f4fd;
            border-left: 4px solid #007bff;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        }
        
        @media (max-width: 768px) {
            .payment-summary {
                grid-template-columns: 1fr;
            }
        }
    `;
    document.head.appendChild(style);
});

// M-Pesa STK Push simulation for development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('Development mode: M-Pesa simulation enabled');
    
    // Mock IntaSend response for development
    window.mockMpesaPayment = function() {
        const event = new Event('submit', { cancelable: true });
        const form = document.getElementById('payment-form');
        
        if (form) {
            // Simulate successful payment after 3 seconds
            setTimeout(() => {
                window.woofcarePayments.showMessage('M-Pesa payment simulation: Enter any PIN on the simulator', 'success');
                
                // Simulate payment completion after another 3 seconds
                setTimeout(() => {
                    window.woofcarePayments.handleSuccessfulPayment('DEV_' + Date.now());
                }, 3000);
            }, 1000);
        }
        
        return false;
    };
    
    // Add development button if in development mode
    document.addEventListener('DOMContentLoaded', function() {
        const paymentForm = document.getElementById('payment-form');
        if (paymentForm) {
            const devButton = document.createElement('button');
            devButton.type = 'button';
            devButton.textContent = 'Simulate M-Pesa Payment (Dev)';
            devButton.style.backgroundColor = '#28a745';
            devButton.style.marginTop = '10px';
            devButton.className = 'btn';
            devButton.onclick = window.mockMpesaPayment;
            
            paymentForm.appendChild(devButton);
        }
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WoofcarePayments;
}