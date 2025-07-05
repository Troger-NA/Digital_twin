class ChatApp {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearChatButton = document.getElementById('clearChat');
        this.logoutButton = document.getElementById('logoutButton');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        
        // Login elements
        this.loginModal = document.getElementById('loginModal');
        this.tokenInput = document.getElementById('tokenInput');
        this.loginButton = document.getElementById('loginButton');
        this.loginError = document.getElementById('loginError');
        this.appContainer = document.getElementById('appContainer');
        
        this.isLoading = false;
        this.messageHistory = [];
        this.sessionId = this.generateSessionId();
        this.authToken = null;
        
        this.initializeEventListeners();
        this.initializeLoginListeners();
        this.updateCurrentTime();
        setInterval(() => this.updateCurrentTime(), 1000);
        
        // Check if user is already logged in
        this.checkStoredToken();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    logClientEvent(eventType, data) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            session_id: this.sessionId,
            event_type: eventType,
            data: data
        };
        
        // Log to console for debugging
        console.log('[CLIENT LOG]', logEntry);
        
        // Store in localStorage for persistence
        try {
            const logs = JSON.parse(localStorage.getItem('client_logs') || '[]');
            logs.push(logEntry);
            // Keep only last 1000 entries
            if (logs.length > 1000) {
                logs.splice(0, logs.length - 1000);
            }
            localStorage.setItem('client_logs', JSON.stringify(logs));
        } catch (e) {
            console.error('Error saving client log:', e);
        }
    }

    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key (but not Shift+Enter)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });

        // Clear chat
        this.clearChatButton.addEventListener('click', () => this.clearChat());
        
        // Logout
        this.logoutButton.addEventListener('click', () => this.logout());
    }

    initializeLoginListeners() {
        // Login button click
        this.loginButton.addEventListener('click', () => this.attemptLogin());
        
        // Login on Enter key
        this.tokenInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.attemptLogin();
            }
        });
    }

    checkStoredToken() {
        const storedToken = localStorage.getItem('authToken');
        if (storedToken) {
            this.authToken = storedToken;
            this.showApp();
        } else {
            this.showLogin();
        }
    }

    async attemptLogin() {
        const token = this.tokenInput.value.trim();
        if (!token) {
            this.showLoginError('Por favor, ingresa un token.');
            return;
        }

        this.loginButton.disabled = true;
        this.loginButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';

        try {
            // Test the token by making a request to the backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': this.sessionId,
                    'X-Auth-Token': token
                },
                body: JSON.stringify({ message: 'test' })
            });

            if (response.ok) {
                // Token is valid
                this.authToken = token;
                localStorage.setItem('authToken', token);
                this.showApp();
                this.logClientEvent('login_success', {
                    timestamp: new Date().toISOString()
                });
            } else {
                // Token is invalid
                this.showLoginError('Token inválido. Por favor, verifica e intenta de nuevo.');
                this.logClientEvent('login_failed', {
                    status: response.status,
                    timestamp: new Date().toISOString()
                });
            }
        } catch (error) {
            console.error('Error during login:', error);
            this.showLoginError('Error de conexión. Por favor, intenta de nuevo.');
            this.logClientEvent('login_error', {
                error: error.message,
                timestamp: new Date().toISOString()
            });
        } finally {
            this.loginButton.disabled = false;
            this.loginButton.innerHTML = '<i class="fas fa-sign-in-alt"></i> Acceder';
        }
    }

    showLogin() {
        this.loginModal.style.display = 'flex';
        this.appContainer.style.display = 'none';
        this.tokenInput.focus();
    }

    showApp() {
        this.loginModal.style.display = 'none';
        this.appContainer.style.display = 'flex';
        this.messageInput.focus();
        
        // Log session start
        this.logClientEvent('session_start', {
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            timestamp: new Date().toISOString()
        });
    }

    showLoginError(message) {
        this.loginError.style.display = 'flex';
        document.getElementById('loginErrorText').textContent = message;
        this.tokenInput.focus();
    }

    logout() {
        this.authToken = null;
        localStorage.removeItem('authToken');
        this.showLogin();
        this.clearChat();
    }

    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const timeElements = document.querySelectorAll('#currentTime');
        timeElements.forEach(el => el.textContent = timeString);
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.sendButton.disabled = true;

        // Show loading indicator
        this.showLoading();

        try {
            const response = await this.callAPI(message);
            this.addMessage(response, 'assistant');
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.', 'assistant');
        } finally {
            this.hideLoading();
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }

    async callAPI(message) {
        const startTime = Date.now();
        
        // Log message sent
        this.logClientEvent('message_sent', {
            message: message,
            timestamp: new Date().toISOString()
        });

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': this.sessionId,
                'X-Auth-Token': this.authToken
            },
            body: JSON.stringify({ message })
        });

        const endTime = Date.now();
        const responseTime = endTime - startTime;

        if (!response.ok) {
            // Log error
            this.logClientEvent('api_error', {
                status: response.status,
                statusText: response.statusText,
                responseTime: responseTime,
                message: message
            });
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Log successful response
        this.logClientEvent('message_received', {
            response: data.response,
            responseTime: responseTime,
            originalMessage: message
        });

        return data.response || 'No se recibió respuesta del servidor.';
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        const icon = document.createElement('i');
        icon.className = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatar.appendChild(icon);

        const content = document.createElement('div');
        content.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.innerHTML = `
            <i class="fas fa-clock"></i>
            <span>${new Date().toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit'
            })}</span>
        `;

        content.appendChild(messageText);
        content.appendChild(messageTime);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Store message in history
        this.messageHistory.push({ text, sender, timestamp: new Date() });
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showLoading() {
        this.isLoading = true;
        this.loadingIndicator.style.display = 'flex';
    }

    hideLoading() {
        this.isLoading = false;
        this.loadingIndicator.style.display = 'none';
    }

    clearChat() {
        if (confirm('¿Estás seguro de que quieres limpiar todo el chat?')) {
            // Log chat clear event
            this.logClientEvent('chat_cleared', {
                messageCount: this.messageHistory.length,
                timestamp: new Date().toISOString()
            });
            
            // Keep only the welcome message
            const welcomeMessage = this.chatMessages.querySelector('.assistant-message');
            this.chatMessages.innerHTML = '';
            if (welcomeMessage) {
                this.chatMessages.appendChild(welcomeMessage);
            }
            
            this.messageHistory = [];
            this.scrollToBottom();
        }
    }

    // Utility method to format timestamps
    formatTimestamp(date) {
        return date.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

// Add some utility functions for better UX
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        const sendButton = document.getElementById('sendButton');
        if (sendButton && !sendButton.disabled) {
            sendButton.click();
        }
    }
});

// Add smooth scrolling for better UX
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.style.scrollBehavior = 'smooth';
    }
}); 