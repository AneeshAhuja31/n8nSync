document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.querySelector('.chat-messages');
    const chatForm = document.querySelector('.chat-input');
    const chatInput = document.querySelector('.chat-input input');
    const newChatBtn = document.querySelector('.nav-links a[href="#"]');
    const historyBtn = document.querySelector('.nav-links a[href="#"]:nth-child(2)');
    
    let currentChatId = null;
    let isLoading = false;
    let chatHistory = [];
    
    initializeChatManagement();
    
    async function initializeChatManagement() {
        try {
            await loadMostRecentChat();
            
            setupEventListeners();
            
            await loadChatHistory(); //in sidebar
            
        } catch (error) {
            console.error('Failed to initialize chat management:', error);
            await createNewChat(); //new chat fallback in case of error
        }
    }
    
    function setupEventListeners() {
        newChatBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await createNewChat();
        });
        
        setupChatHistoryInterface();
        
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!checkApiKeysBeforeChat()) {
                return;
            }
            
            const message = chatInput.value.trim();
            if (!message || isLoading) return;
            
            await sendMessage(message);
        });
    }
    
    function setupChatHistoryInterface() {
        const historyContainer = document.createElement('div');
        historyContainer.className = 'chat-history-container';
        historyContainer.innerHTML = `
            <div class="chat-history-header">
                <h3>Chat History</h3>
                <button class="refresh-chats-btn" title="Refresh">
                    <i class="fas fa-refresh"></i>
                </button>
            </div>
            <div class="chat-history-list" id="chatHistoryList">
                <div class="chat-history-loading">
                    <div class="loader-spinner"></div>
                    <p>Loading chats...</p>
                </div>
            </div>
        `;
        
        historyBtn.parentNode.replaceChild(historyContainer, historyBtn);
        
        const refreshBtn = historyContainer.querySelector('.refresh-chats-btn');
        refreshBtn.addEventListener('click', async () => {
            await loadChatHistory();
        });
    }
    
    async function loadMostRecentChat() {
        try {
            showLoader('Loading recent chat...');
            
            const response = await fetch('http://localhost:8000/chat/recent', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load recent chat');
            }
            
            const data = await response.json();
            currentChatId = data.chat_id;
            
            await loadChatMessages(currentChatId);
            
        } catch (error) {
            console.error('Error loading recent chat:', error);
            hideLoader();
            throw error;
        }
    }
    
    async function createNewChat() {
        try {
            showLoader('Creating new chat...');
            
            const response = await fetch('http://localhost:8000/chat/new', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to create new chat');
            }
            
            const data = await response.json();
            currentChatId = data.chat_id;
            
            clearChatMessages();
            
            await loadChatHistory();
            
            showWelcomeMessage();
            
            hideLoader();
            
        } catch (error) {
            console.error('Error creating new chat:', error);
            hideLoader();
            alert('Failed to create new chat. Please try again.');
        }
    }
    
    async function loadChatHistory() {
        try {
            const response = await fetch('http://localhost:8000/chat/list', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load chat history');
            }
            
            const data = await response.json();
            chatHistory = data.chats;
            
            renderChatHistory();
            
        } catch (error) {
            console.error('Error loading chat history:', error);
            renderChatHistoryError();
        }
    }
    
    function renderChatHistory() {
        const chatHistoryList = document.getElementById('chatHistoryList');
        
        if (chatHistory.length === 0) {
            chatHistoryList.innerHTML = `
                <div class="no-chats">
                    <p>No chat history yet</p>
                </div>
            `;
            return;
        }
        
        chatHistoryList.innerHTML = chatHistory.map(chat => `
            <div class="chat-history-item ${chat.id === currentChatId ? 'active' : ''}" 
                 data-chat-id="${chat.id}">
                <div class="chat-info">
                    <div class="chat-title" title="${chat.title}">
                        ${chat.title}
                    </div>
                    
                </div>
                <div class="chat-actions">
                    <button class="edit-chat-btn" title="Edit title" data-chat-id="${chat.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-chat-btn" title="Delete chat" data-chat-id="${chat.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        addChatHistoryEventListeners();
    }
    
    function addChatHistoryEventListeners() {
        const chatItems = document.querySelectorAll('.chat-history-item');
        const editBtns = document.querySelectorAll('.edit-chat-btn');
        const deleteBtns = document.querySelectorAll('.delete-chat-btn');
        
        chatItems.forEach(item => {
            item.addEventListener('click', async (e) => {
                if (e.target.closest('.chat-actions')) return;
                
                const chatId = item.dataset.chatId;
                if (chatId !== currentChatId) {
                    await switchToChat(chatId);
                }
            });
        });
        
        editBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const chatId = btn.dataset.chatId;
                await editChatTitle(chatId);
            });
        });
        
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const chatId = btn.dataset.chatId;
                await deleteChatConfirm(chatId);
            });
        });
    }
    
    async function switchToChat(chatId) {
        if (isLoading) return;
        
        try {
            showLoader('Loading chat...');
            
            currentChatId = chatId;
            
            //update active chat in history
            updateActiveChatInHistory(chatId);
            
            //load messages for this chat
            await loadChatMessages(chatId);
            
        } catch (error) {
            console.error('Error switching to chat:', error);
            hideLoader();
            alert('Failed to load chat. Please try again.');
        }
    }
    
    async function loadChatMessages(chatId) {
        try {
            const response = await fetch(`http://localhost:8000/chat/${chatId}/messages`, {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load chat messages');
            }
            
            const data = await response.json();
            
            //clear existing messages
            clearChatMessages();
            
            //render messages
            if (data.messages.length === 0) {
                showWelcomeMessage();
            } else {
                data.messages.forEach(message => {
                    if (message.role === 'assistant') {
                        const messageDiv = addMessage('', message.role, false);
                        const answerContainer = createAnswerContainer(messageDiv);
                        const renderedContent = renderMarkdown(message.content);
                        answerContainer.innerHTML = renderedContent;
                    } else {
                        addMessage(message.content, message.role, false);
                    }
                });
            }
            
            hideLoader();
            
        } catch (error) {
            console.error('Error loading chat messages:', error);
            hideLoader();
            throw error;
        }
    }
    
    async function sendMessage(message) {
        if (!currentChatId) {
            await createNewChat();
        }
        
        // Add user message to UI
        addMessage(message, 'user');
        chatInput.value = '';
        
        // Create agent response container
        const agentMessageDiv = addMessage('', 'agent');
        
        // Start SSE stream
        await streamResponse(message, agentMessageDiv);
        
        // Refresh chat history to update last accessed time
        await loadChatHistory();
    }
    
    async function editChatTitle(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;
        
        const newTitle = prompt('Enter new chat title:', chat.title);
        if (newTitle && newTitle.trim() !== chat.title) {
            try {
                const response = await fetch(`http://localhost:8000/chat/${chatId}/title`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ title: newTitle.trim() })
                });
                
                if (response.ok) {
                    await loadChatHistory();
                } else {
                    alert('Failed to update chat title');
                }
            } catch (error) {
                console.error('Error updating chat title:', error);
                alert('Failed to update chat title');
            }
        }
    }
    
    async function deleteChatConfirm(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;
        
        try {
            const response = await fetch(`http://localhost:8000/chat/${chatId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                // If deleting current chat, switch to most recent or create new
                if (chatId === currentChatId) {
                    await loadMostRecentChat();
                }
                
                await loadChatHistory();
            } else {
                alert('Failed to delete chat');
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            alert('Failed to delete chat');
        }
        
    }
    
    function updateActiveChatInHistory(chatId) {
        const chatItems = document.querySelectorAll('.chat-history-item');
        chatItems.forEach(item => {
            if (item.dataset.chatId === chatId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    function clearChatMessages() {
        chatMessages.innerHTML = '';
    }
    
    function showWelcomeMessage() {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'message agent';
        welcomeDiv.id = 'welcome';
        welcomeDiv.innerHTML = `
            <div class="welcome-content">
                <h3 style="margin-bottom: -2.0rem">Welcome ${localStorage.getItem("userName")}</h3>
                <p>How can I assist you today?</p>
            </div>
        `;
        chatMessages.appendChild(welcomeDiv);
    }
    
    function showLoader(message = 'Loading...') {
        isLoading = true;
        
        // Show loader in chat area
        const loaderDiv = document.createElement('div');
        loaderDiv.className = 'chat-loader';
        loaderDiv.id = 'chatLoader';
        loaderDiv.innerHTML = `
            <div class="spinner"></div>
            <p class="loader-text">${message}</p>
        `;
        
        chatMessages.appendChild(loaderDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    
    function hideLoader() {
        isLoading = false;
        const loader = document.getElementById('chatLoader');
        if (loader) {
            loader.remove();
        }
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
    
    function renderChatHistoryError() {
        const chatHistoryList = document.getElementById('chatHistoryList');
        chatHistoryList.innerHTML = `
            <div class="chat-history-error">
                <p>Failed to load chat history</p>
                <button class="retry-btn" onclick="loadChatHistory()">Retry</button>
            </div>
        `;
    }
    
    function addMessage(content, role, shouldScroll = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        if (content) messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        
        if (shouldScroll) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        return messageDiv;
    }
    
    function createThoughtsContainer(parentDiv) {
        const thoughtsContainer = document.createElement('div');
        thoughtsContainer.className = 'thoughts-container';
        thoughtsContainer.innerHTML = `
            <div class="thoughts-header" onclick="toggleThoughts(this)">
                <span class="thoughts-toggle">▽ Thinking...</span>
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
    
    function formatJsonInContent(content) {
        const jsonRegex = /```json\s*([\s\S]*?)\s*```|json```\s*([\s\S]*?)\s*```/g;
        
        return content.replace(jsonRegex, (match, jsonContent1, jsonContent2) => {
            const trimmedJson = (jsonContent1 || jsonContent2).trim();
            
            try {
                const parsed = JSON.parse(trimmedJson);
                const formattedJson = JSON.stringify(parsed, null, 2);
                
            return `<div class="code-template-container" style="max-width: 90%; margin: auto;">
                    <div class="code-template-header">
                        <span class="code-template-title">JSON</span>
                        <button class="copy-code-btn" onclick="copyToClipboard(this)" data-code="${btoa(formattedJson)}">
                            <i class="fas fa-copy"></i> Copy JSON
                        </button>
                    </div>
                    <div class="code-template-content">
                        <pre><code class="json-code">${escapeHtml(formattedJson)}</code></pre>
                    </div>
                </div>`;
            } catch (e) {
                return `<div class="code-template-container">
                    <div class="code-template-header">
                        <span class="code-template-title">Code Block</span>
                        <button class="copy-code-btn" onclick="copyToClipboard(this)" data-code="${btoa(trimmedJson)}">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <div class="code-template-content">
                        <pre><code>${escapeHtml(trimmedJson)}</code></pre>
                    </div>
                </div>`;
            }
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function renderMarkdown(text) {
        const jsonBlocks = [];
        let jsonIndex = 0;
        
        text = text.replace(/```json\s*([\s\S]*?)\s*```|json```\s*([\s\S]*?)\s*```/g, (match) => {
            const placeholder = `__JSON_BLOCK_${jsonIndex}__`;
            jsonBlocks[jsonIndex] = match;
            jsonIndex++;
            return placeholder;
        });
        
        text = text
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
            .replace(/^[\s]*[-*+][\s]+(.*)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        if (!text.startsWith('<h') && !text.startsWith('<ul') && !text.startsWith('<ol')) {
            text = '<p>' + text + '</p>';
        }
        
        jsonBlocks.forEach((block, index) => {
            const placeholder = `__JSON_BLOCK_${index}__`;
            const formattedBlock = formatJsonInContent(block);
            text = text.replace(placeholder, formattedBlock);
        });
        
        return text;
    }


    async function streamResponse(message, agentMessageDiv) {
        let thoughtsContainer = null;
        let answerContainer = null;
        let fullAnswerContent = '';
        let streamingLoader = null;

        streamingLoader = document.createElement('div');
        streamingLoader.className = 'streaming-loader';
        streamingLoader.innerHTML = `
            <div class="streaming-dot"></div>
        `;
        agentMessageDiv.appendChild(streamingLoader);

        try {
            let n8nUri = "http://localhost:5678"
            let n8nInstanceType = localStorage.getItem("n8nInstanceType")
            if (n8nInstanceType === "cloud"){
                n8nUri = localStorage.getItem("n8nCloudUri")
            }
            else if(n8nInstanceType === "localhost"){
                n8nUri = "http://localhost:5678";
            }
            else{
                showApiKeyOverlay();
            }

            const response = await fetch('http://localhost:8000/agent/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    message: message,
                    chat_id: currentChatId,
                    n8n_api_key : localStorage.getItem("n8nApiKey"),
                    gemini_api_key : localStorage.getItem("geminiApiKey"),
                    n8n_uri:n8nUri
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
                            
                            if ((data.type === 'thought' || data.type === 'observation' || data.type === 'error') && !thoughtsContainer) {
                                thoughtsContainer = createThoughtsContainer(agentMessageDiv);
                            }
                            
                            if ((data.type === 'token' || data.type === 'final_answer_start') && !answerContainer) {
                                answerContainer = createAnswerContainer(agentMessageDiv);
                            }
                            
                            // Remove loader only on final_answer_start
                            if (data.type === 'final_answer_start' && streamingLoader) {
                                streamingLoader.remove();
                                streamingLoader = null;
                            }
                            
                            handleStreamData(data, thoughtsContainer, answerContainer);
                            
                            if (data.type === 'token') {
                                fullAnswerContent += data.content;
                            }
                            if(data.type === 'invalid_api_key'){
                                if(streamingLoader){
                                    streamingLoader.remove();
                                    streamingLoader = null;
                                }
                                agentMessageDiv.innerHTML = `
                                    <div class="error-message">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        ${data.content}
                                    </div>
                                `;
                                showApiKeyOverlay();
                                return;
                            }
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
            
            if (answerContainer && fullAnswerContent) {
                const renderedContent = renderMarkdown(fullAnswerContent);
                answerContainer.innerHTML = renderedContent;
            }
            
        } catch (error) {
            // Remove loader on error
            if (streamingLoader) {
                streamingLoader.remove();
            }
            
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
                    const currentContent = answerContainer.textContent || '';
                    answerContainer.textContent = currentContent + data.content;
                }
                break;
            case 'error':
                if (thoughtsContainer) {
                    addThought(thoughtsContainer, data.content, 'error');
                }
                break;
            case 'final_answer_start':
                if (answerContainer) {
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
    
    // Global functions
    window.toggleThoughts = function(header) {
        const thoughtsContainer = header.parentElement;
        const content = thoughtsContainer.querySelector('.thoughts-content');
        const toggle = header.querySelector('.thoughts-toggle');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▽ Thinking...';
            thoughtsContainer.classList.remove('collapsed');
        } else {
            content.style.display = 'none';
            toggle.textContent = '▷ Thinking...';
            thoughtsContainer.classList.add('collapsed');
        }
    };
    
    window.copyToClipboard = async function(button) {
        const encodedCode = button.getAttribute('data-code');
        const code = atob(encodedCode);
        
        try {
            await navigator.clipboard.writeText(code);
            
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);
            
        } catch (err) {
            console.error('Failed to copy text: ', err);
            
            const textArea = document.createElement('textarea');
            textArea.value = code;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);
        }
    };

    function checkApiKeysBeforeChat() {
        const n8nApiKey = localStorage.getItem('n8nApiKey');
        const geminiApiKey = localStorage.getItem('geminiApiKey');
        
        if (!n8nApiKey || !geminiApiKey) {
            showApiKeyOverlay();
            return false;
        }
        return true;
    }
    
    // Make loadChatHistory available globally for retry button
    window.loadChatHistory = loadChatHistory;
});