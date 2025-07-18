# n8nSync

n8nSync is an agentic application that transforms workflow automation through natural conversation. Powered by AI agents and seamless integration with the n8n platform, it enables users to create, manage, and optimize complex workflows effortlessly.

## Key Features

- **Conversational Workflow Automation:** Build and modify workflows using a chat-based interface, making automation accessible for all skill levels.
- **Agentic Intelligence:** AI agents (LangChain + Gemini) analyze workflows, provide actionable insights, and suggest optimizations in real time.
- **Live Collaboration:** Interact with workflows, ask questions, and receive instant feedback—just like chatting with a colleague.
- **Secure API Integration:** Connect to n8n and Gemini APIs with robust error handling and retry logic. API keys are stored locally in your browser for maximum privacy.
- **Google OAuth Authentication:** Authenticate securely using Google OAuth; credentials are protected and never exposed.
- **Privacy First:** Your workflow data remains in your n8n instance—never stored or accessed by n8nSync.

## Click on this image to see demo:

[![Watch the demo](https://img.youtube.com/vi/xCQmBvU8PRU/0.jpg)](https://www.youtube.com/watch?v=xCQmBvU8PRU)

## Getting Started

1. **Sign Up:** Use Google OAuth for secure authentication.
2. **Configure:** Manage your workflows and API keys from the dashboard.
3. **Automate:** Start building and optimizing workflows via natural conversation.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastApi
- **AI/Agents:** LangChain, Gemini API
- **Integration:** n8n platform
- **Authentication:** Google OAuth 2.0

## Install
```sh
git clone https://github.com/yourusername/n8nSync.git
cd n8nSync/server
pip install -r requirements.txt
```
## Run
```sh
cd n8nSync/server 
uvicorn app:app --reload
```


## License

MIT License © 2025