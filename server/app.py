from fastapi import FastAPI,Request,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse,RedirectResponse,JSONResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_callback_handler import CustomCallBackHandler
from asyncio import Queue
import asyncio
import os
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
from workflow_tools import *
from pydantic_models import ChatMessage, ChatHistoryResponse
from prompt_templates import combined_react_prompt
from langchain.agents import create_react_agent,AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnableConfig
import httpx
from middleware_jwt import create_jwt_token,verify_jwt_token,JWT_EXPIRATION_HOURS
from db.user_db import create_or_update_user,set_user_inactive

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
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

SCOPES = "openid email profile"

llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.5-flash",
    temperature=0.3
)

tools = [
    fetch_existing_workflow,
    get_all_existing_workflows,
    create_workflow_from_prompt,
    explain_workflow,  
    modify_workflow
] 

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=combined_react_prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    early_stopping_method="force"
)

@app.get("/")
async def root():
    return {"message": "n8n Agentic Workflow Builder"}

@app.get("/login")
async def login():
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(google_auth_url)

@app.get("/auth/callback")
async def auth_callback(request:Request):
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(url="http://localhost:3000/error.html")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url,data=data)
        token_json = token_response.json()
    
    access_token = token_json.get('access_token')

    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        userinfo = userinfo_response.json()

    user_data = {
        "name":userinfo.get('name'),
        "email":userinfo.get('email')
    }
    response = await create_or_update_user(user_data)
    if response:
        print("User Inserted")
    else:
        print("User Updated")

    jwt_token = create_jwt_token(user_data)
    response = RedirectResponse(f"http://localhost:3000/dashboard.html")
    response.set_cookie(
        key="auth_token",
        value=jwt_token,
        httponly=True,
        secure=False, #set to true in prod
        samesite="lax",
        max_age=JWT_EXPIRATION_HOURS*3600
    )
    return response

@app.get("/auth/validate")
async def validate_token(request:Request):
    token = request.cookies.get("auth_token")
    if not token:  #check if token exists
        raise HTTPException(status_code=401, detail="No token provided")
    try:
        payload = verify_jwt_token(token)
        return {
            "valid":True,
            "user":{
                "name":payload.get("name"),
                "email":payload.get("email")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401,detail=str(e))

@app.post("/auth/logout")
async def logout(request:Request):
    response_dict = await request.json()
    inactive_response = await set_user_inactive(response_dict["email"])
    if(inactive_response):
        print("User logged out")
    else: print("Unable to logout")
    response = {"message":"Logged out successfully"}
    response = JSONResponse(content=response)
    response.delete_cookie("auth_token")
    return response

@app.post("/agent/stream")
async def stream_agent_response(chat_input: ChatMessage):
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
        agent_response = ""
        
        try:
            agent_task = asyncio.create_task(
                agent_executor.ainvoke(
                    {
                        "input": user_message,
                    },
                    config=config
                )
            )

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
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
            
            # Get final result if not already processed
            if not agent_task.done():
                try:
                    final_result = await agent_task
                    if isinstance(final_result, dict) and 'output' in final_result and not agent_response:
                        agent_response = final_result['output']
                    elif isinstance(final_result, str) and not agent_response:
                        agent_response = final_result
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Agent error: {str(e)}'})}\n\n"
            
            # Save to chat history
            chat_sessions[session_id].append({
                "role": "assistant", 
                "content": agent_response.strip() if agent_response else "",
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