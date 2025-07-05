document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.querySelector('.chat-messages');
    const chatForm = document.querySelector('.chat-input');
    const chatInput = document.querySelector('.chat-input input');
    
    let currentSessionId = 'default';
    
    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to UI
        addMessage(message, 'user');
        chatInput.value = '';
        
        // Create agent response container (initially empty)
        const agentMessageDiv = addMessage('', 'agent');
        
        // Start SSE stream
        await streamResponse(message, agentMessageDiv);
    });
    
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        if (content) messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }
    
    function createThoughtsContainer(parentDiv) {
        const thoughtsContainer = document.createElement('div');
        thoughtsContainer.className = 'thoughts-container';
        thoughtsContainer.innerHTML = `
            <div class="thoughts-header" onclick="toggleThoughts(this)">
                <span class="thoughts-label">Thinking...</span>
                <span class="thoughts-toggle">▼</span>
            </div>
            <div class="thoughts-content">
                <div class="thoughts-list"></div>
            </div>
        `;
        parentDiv.appendChild(thoughtsContainer);
        return thoughtsContainer.querySelector('.thoughts-list');
    }
    
    function createAnswerContainer(parentDiv) {
        const answerContainer = document.createElement('div');
        answerContainer.className = 'answer-container';
        answerContainer.innerHTML = '<div class="answer-content"></div>';
        parentDiv.appendChild(answerContainer);
        return answerContainer.querySelector('.answer-content');
    }
    
    async function streamResponse(message, agentMessageDiv) {
        let thoughtsContainer = null;
        let answerContainer = null;
        
        try {
            const response = await fetch('http://localhost:8000/agent/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: currentSessionId
                })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            // Create containers only when needed
                            if ((data.type === 'thought' || data.type === 'observation' || data.type === 'error') && !thoughtsContainer) {
                                thoughtsContainer = createThoughtsContainer(agentMessageDiv);
                            }
                            
                            if ((data.type === 'token' || data.type === 'final_answer_start') && !answerContainer) {
                                answerContainer = createAnswerContainer(agentMessageDiv);
                            }
                            
                            handleStreamData(data, thoughtsContainer, answerContainer);
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } catch (error) {
            if (!answerContainer) {
                answerContainer = createAnswerContainer(agentMessageDiv);
            }
            answerContainer.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
        }
    }
    
    function handleStreamData(data, thoughtsContainer, answerContainer) {
        switch (data.type) {
            case 'thought':
                if (thoughtsContainer) {
                    addThought(thoughtsContainer, data.content, 'thought');
                }
                break;
            case 'observation':
                if (thoughtsContainer) {
                    addThought(thoughtsContainer, data.content, 'observation');
                }
                break;
            case 'token':
                if (answerContainer) {
                    // Stream tokens directly to answer
                    answerContainer.innerHTML += data.content;
                }
                break;
            case 'error':
                if (thoughtsContainer) {
                    addThought(thoughtsContainer, data.content, 'error');
                }
                break;
            case 'final_answer_start':
                if (answerContainer) {
                    // Clear answer container and prepare for streaming
                    answerContainer.innerHTML = '';
                }
                break;
        }
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addThought(container, content, type) {
        const thoughtDiv = document.createElement('div');
        thoughtDiv.className = `thought-item ${type}`;
        thoughtDiv.textContent = content;
        container.appendChild(thoughtDiv);
    }
    
    // Global function for toggling thoughts
    window.toggleThoughts = function(header) {
        const thoughtsContainer = header.parentElement;
        const content = thoughtsContainer.querySelector('.thoughts-content');
        const toggle = header.querySelector('.thoughts-toggle');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▼';
            thoughtsContainer.classList.remove('collapsed');
        } else {
            content.style.display = 'none';
            toggle.textContent = '▶';
            thoughtsContainer.classList.add('collapsed');
        }
    };
});