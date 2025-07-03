document.addEventListener("DOMContentLoaded",()=>{
    const chatMessages = document.querySelector(".chat-messages")
    const chatForm = document.querySelector(".chat-input")
    const chatInput = document.querySelector(".chat-input input")

    let currentSessionId = 'default' 

    //Handle form submission
    chatForm.addEventListener('submit',async (e)=>{
        e.preventDefault()
        const message = chatInput.value.trim()
        if (!message) return

        // Add user message to ui
        addMessage(message,'user')
        chatInput.value = ''

        //Create agent response container
        const agentMessageDiv = addMessage('','agent')
        const thoughtsContainer = createThoughtsContainer(agentMessageDiv)
        const answerContainer = createAnswerContainer(agentMessageDiv)

        //Start SSE stream
        await streamResponse(message,thoughtsContainer,answerContainer)
    })

    function addMessage(content,role){
        const messageDiv = document.createElement('div')
        messageDiv.className = `message ${role}`
        if (content) messageDiv.textContent = content
        chatMessages.appendChild(messageDiv)
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function createThoughtsContainer(parentDiv){
        parentDiv.innerHTML = `
            <div class="thoughts-container">
                <div class="thoughts-header" onclick="toggleThoughts(this)">
                    <span>🤔 Agent Thoughts</span>
                    <span class="arrow">▼</span>
                </div>
                <div class="thoughts-content" style="display: none;">
                    <div class="thoughts-list"></div>
                </div>
            </div>
            <div class="answer-container">
                <div class="answer-label">💬 Answer:</div>
                <div class="answer-content"></div>
            </div>
        `
        return parentDiv.querySelector('.thougts-list')
    }

    function createAnswerContainer(parentDiv){
        return parentDiv.querySelector('.answer-content')
    }

    async function streamResponse(message,thoughtsContainer,answerContainer) {
        try{
            const response = await fetch('/chat/stream',{
                method:'POST',
                headers: {
                    'Content-Type':'application/json',
                },
                body: JSON.stringify({
                    message:message,
                    session_id:currentSessionId
                })
            })
            const reader = response.body.getReader()
            const decoder = new TextDecoder()

            while(true){
                const {done,value} = await reader.read()
                if(done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for(const line of lines){
                    if(line.startsWith('data: ')){
                        try {
                            const data = JSON.parse(line.slice(6))
                            handleStreamData(data,thoughtsContainer,answerContainer)
                        }
                        catch(e){
                            console.warn('Failed to parse SSE data:',line)
                        }
                    }
                }
            }
        }
        catch(error){
            answerContainer.textContent = `Error: ${error.message}`
        }
    }
    function handleStreamData(data,thoughtsContainer,answerContainer){
        switch(data.type){
            case 'thought':
                addThought(thoughtsContainer,data.content,'thought')
                break
            case 'observation':
                addThought(thoughtsContainer,data.content,'observation')
                break
            case 'token':
                //Stream tokens directly to answer/no collection
                answerContainer.textContent += data.content
                break
            case 'error':
                addThought(thoughtsContainer,data.content,'error')
                break
            case 'final_answer_start':
                // Clear answer container and prepare for streaming
                answerContainer.textContent = ''
                break
        }
        chatMessages.scrollTop = chatMessages.scrollHeight
    }
    function addThought(container,content,type){
        const thoughtDiv = document.createElement('div')
        thoughtDiv.className = `thought ${type}`
        thoughtDiv.textContent = content
        container.appendChild(thoughtDiv)

        // Show thoughts container if it's hidden
        const thoughtsContent = container.closest('.thoughts-content')
        if (thoughtsContent && thoughtsContent.style.display === 'none') {
            thoughtsContent.style.display = 'block'
            const arrow = thoughtsContent.previousElementSibling.querySelector('.arrow')
            if (arrow) arrow.textContent = '▲'
        }    
    }
    window.toggleThoughts = function(header) {
        const content = header.nextElementSibling
        const arrow = header.querySelector('.arrow')
        if (content.style.display === 'none') {
            content.style.display = 'block'
            arrow.textContent = '▲'
        } else {
            content.style.display = 'none'
            arrow.textContent = '▼'
        }
    }
})