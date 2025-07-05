from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_callback_handler import CustomCallBackHandler
from asyncio import Queue
import asyncio
import os
from dotenv import load_dotenv
from workflow_tools import *
from prompt_templates import system_prompt_template
from pydantic_models import ChatMessage,ChatHistoryResponse
from langchain.agents import initialize_agent,AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnableConfig
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Chat history storage (in production, use a database)
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.5-flash",
    temperature = 0.3
)

tools = [
    fetch_exisiting_workflow,
    get_all_exisiting_workflows,
    create_workflow_from_prompt,
    explain_workflow,
    modify_workflow
]

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)

agent = initialize_agent(
    llm = llm,
    tools=tools,
    return_intermediate_steps=True,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    system_message=system_prompt_template.format(),
    verbose=True,
    handle_parsing_errors= True, 
)

@app.get("/")
async def root():
    return {"message":"n8n Agentic Workflow Builder"}

@app.post("/agent/stream")
async def stream_agent_response(chat_input:ChatMessage):
    session_id = chat_input.session_id
    user_message = chat_input.message

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # Add user message to chat history
    chat_sessions[session_id].append({
        "role": "user",
        "content": user_message,
        "timestamp": asyncio.get_event_loop().time()
    })
    queue = Queue()
    cb_handler = CustomCallBackHandler(queue)
    config = RunnableConfig(callbacks=[cb_handler])
    async def generate_response():
        try:
            agent_task = asyncio.create_task(
                agent.ainvoke(
                    {"input": user_message},
                    config=config
                )
                #agent.arun(input=user_message,callbacks=[cb_handler])
            )

            agent_response = ""

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(),timeout=1.0)
                    data = json.loads(message)

                    if data["type"] == "token":
                        agent_response += data["content"]
                        yield f"data: {message}\n\n"
                    
                    elif data["type"] in ["thought", "observation", "error", "final_answer_start", "final_answer_end"]:
                        yield f"data: {message}\n\n"
                        
                    elif data["type"] == "end":
                        yield f"data: {message}\n\n"
                        break
                
                except asyncio.TimeoutError:
                    if agent_task.done():
                        break
                    continue
                
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                    break
            
            if not agent_task.done():
                try:
                    final_result = await agent_task
                    if isinstance(final_result, str):
                        agent_response = final_result
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Agent error: {str(e)}'})}\n\n"
            
            chat_sessions[session_id].append({
                "role": "assistant", 
                "content": agent_response.strip(),
                "timestamp": asyncio.get_event_loop().time()
            })
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Stream error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    if session_id not in chat_sessions:
        return ChatHistoryResponse(session_id=session_id, messages=[])
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=chat_sessions[session_id]
    )

@app.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    memory.clear()
    return {"message": f"Chat history cleared for session {session_id}"}

@app.get("/chat/sessions")
async def get_all_sessions():
    return {"sessions": list(chat_sessions.keys())}
            
