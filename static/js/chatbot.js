document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const questionnaire = document.getElementById('chat-questionnaire');
    const questionnaireForm = document.getElementById('questionnaire-form');

    // Show questionnaire first
    questionnaire.classList.remove('d-none');

    questionnaireForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(questionnaireForm);
        const userType = formData.get('user_type');

        // Store user type in session storage
        sessionStorage.setItem('user_type', userType);

        // Hide questionnaire and enable chat
        questionnaire.classList.add('d-none');
        chatInput.disabled = false;
        sendButton.disabled = false;

        // Add welcome message based on user type
        const welcomeMessage = `Welcome! I see you're a ${userType}. How can I assist you today?`;
        addMessage(welcomeMessage);
    });

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <span class="message-text">${message}</span>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage(message) {
        addMessage(message, true);

        try {
            const response = await fetch('/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    user_type: sessionStorage.getItem('user_type')
                })
            });

            const data = await response.json();
            addMessage(data.response);

            // If response suggests booking a meeting, show suggestion
            if (data.suggest_meeting) {
                addMessage("Would you like to schedule a meeting to discuss this further? Click here to book an appointment.", false);
                const bookingLink = document.createElement('div');
                bookingLink.className = 'chat-message bot-message';
                bookingLink.innerHTML = `
                    <div class="message-content">
                        <a href="/appointment" class="btn btn-success btn-sm">
                            <i class="bi bi-calendar-check"></i> Schedule Meeting
                        </a>
                    </div>
                `;
                chatMessages.appendChild(bookingLink);
            }
        } catch (error) {
            addMessage('Sorry, I encountered an error. Please try again.');
        }
    }

    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
            chatInput.value = '';
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });
});