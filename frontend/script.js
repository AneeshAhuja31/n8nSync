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
        // Look for both ```json and json``` patterns
        const jsonRegex = /```json\s*([\s\S]*?)\s*```|json```\s*([\s\S]*?)\s*```/g;
        
        return content.replace(jsonRegex, (match, jsonContent1, jsonContent2) => {
            // Use whichever capture group matched
            const trimmedJson = (jsonContent1 || jsonContent2).trim();
            
            try {
                // Try to parse and format the JSON
                const parsed = JSON.parse(trimmedJson);
                const formattedJson = JSON.stringify(parsed, null, 2);
                
                return `<div class="code-template-container">
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
                // If JSON parsing fails, display as plain text
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

    // Enhanced function to detect any JSON-like content in the response
    function detectAndFormatJson(content) {
        // First try the markdown code block detection
        let processedContent = formatJsonInContent(content);
        
        // If no markdown code blocks found, try to detect standalone JSON objects
        if (processedContent === content) {
            // Look for JSON object patterns (starting with { and ending with })
            const jsonObjectRegex = /(\{[\s\S]*?\})/g;
            
            processedContent = content.replace(jsonObjectRegex, (match, jsonCandidate) => {
                // Only process if it looks like a substantial JSON object (more than just {})
                if (jsonCandidate.length > 10) {
                    try {
                        const parsed = JSON.parse(jsonCandidate);
                        // Check if it's likely an n8n workflow (has nodes, connections, etc.)
                        if (parsed.nodes && parsed.connections) {
                            const formattedJson = JSON.stringify(parsed, null, 2);
                            
                            return `<div class="code-template-container">
                                <div class="code-template-header">
                                    <span class="code-template-title">n8n Workflow JSON</span>
                                    <button class="copy-code-btn" onclick="copyToClipboard(this)" data-code="${btoa(formattedJson)}">
                                        <i class="fas fa-copy"></i> Copy JSON
                                    </button>
                                </div>
                                <div class="code-template-content">
                                    <pre><code class="json-code">${escapeHtml(formattedJson)}</code></pre>
                                </div>
                            </div>`;
                        }
                    } catch (e) {
                        // Not valid JSON, return original
                    }
                }
                return match;
            });
        }
        
        return processedContent;
    }

    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async function streamResponse(message, agentMessageDiv) {
        let thoughtsContainer = null;
        let answerContainer = null;
        let fullAnswerContent = '';
        
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
                            
                            // Collect full answer content for final processing
                            if (data.type === 'token') {
                                fullAnswerContent += data.content;
                            }
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
            
            // Process the final answer for JSON code blocks
            if (answerContainer && fullAnswerContent) {
                const processedContent = detectAndFormatJson(fullAnswerContent);                answerContainer.innerHTML = processedContent;
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
                    // For streaming, we'll just accumulate the text
                    // The final processing will handle JSON formatting
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
        const code = atob(encodedCode); // Decode the base64 encoded JSON
        
        try {
            await navigator.clipboard.writeText(code);
            
            // Visual feedback
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);
            
        } catch (err) {
            console.error('Failed to copy text: ', err);
            
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = code;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Visual feedback
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);
        }
    };
});