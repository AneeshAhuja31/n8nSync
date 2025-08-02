from fastapi import FastAPI,Request,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse,RedirectResponse,JSONResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import InvalidArgument
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from custom_callback_handler import CustomCallBackHandler
from asyncio import Queue
import asyncio
import os
import json
from dotenv import load_dotenv
from workflow_tools import (wrapper_fetch_existing_workflow,wrapper_get_all_existing_workflows,
                            wrapper_post_worflow,create_workflow_from_prompt,
                            explain_workflow,modify_workflow
                        )
from pydantic_models import ChatMessage
from prompt_templates import combined_react_prompt
from langchain.agents import create_react_agent,AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_core.runnables import RunnableConfig
import httpx
from middleware_jwt import create_jwt_token,verify_jwt_token,get_user_from_token,JWT_EXPIRATION_HOURS
from db.user_db import create_or_update_user,set_user_inactive
import requests
from requests.exceptions import ConnectionError
from db.chat_and_message_db import (
    create_new_chat, get_user_chats, get_most_recent_chat,
    update_chat_access, save_message, get_chat_messages,
    delete_chat, update_chat_title
)
import uvicorn
load_dotenv()
app = FastAPI()
server_uri = os.getenv("SERVER_URI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://n8nsync.aneeshahuja.tech","https://n8nsync.vercel.app", server_uri], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY")
TURNSTILE_SITE_SECRET = os.getenv("TURNSTILE_SITE_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

SCOPES = "openid email profile"

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

async def create_agent_executor(gemini_api_key,tools):
    parser = ReActSingleInputOutputParser()

    llm = ChatGoogleGenerativeAI(
        api_key=gemini_api_key,
        model="gemini-2.5-flash",
        temperature=0.3
    )
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=combined_react_prompt,
        output_parser=parser
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        early_stopping_method="force",
        max_iterations=6
    )
    return agent_executor

@app.get("/")
async def root():
    return {"message": "n8n Agentic Workflow Builder"}

@app.get("/login")
async def login(request:Request):
    captcha_token = request.query_params.get("captchaToken")
    if not captcha_token:
        raise HTTPException(status_code=400, detail="Missing CAPTCHA token")
    
    verification_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": TURNSTILE_SITE_SECRET,
        "response": captcha_token,
        "remoteip": request.client.host
    }
    r = requests.post(verification_url, data=data)
    result = r.json()

    if not result.get("success"):
        raise HTTPException(status_code=403, detail="CAPTCHA verification failed")
    print("CloudFlare Success")
    
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

    jwt_token = create_jwt_token(user_data)
    response = RedirectResponse(f"https://n8nsync.aneeshahuja.tech/chat.html")
    response.set_cookie(
        key="auth_token",
        value=jwt_token,
        httponly=True,
        secure=True, #set to true in prod
        samesite="none",#changed from "lax" to "none" for cross-origin
        max_age=JWT_EXPIRATION_HOURS*3600,
        #domain=".onrender.com"
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
    response = {"message":"Logged out successfully"}
    response = JSONResponse(content=response)
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        secure=True,
        samesite="none"
    )
    return response

async def load_chat_into_memory(chat_id: str):
    memory.clear()  
    
    messages = await get_chat_messages(chat_id)
    
    for message in messages:
        if message["role"] == "user":
            memory.chat_memory.add_user_message(message["content"])
        elif message["role"] == "assistant":
            memory.chat_memory.add_ai_message(message["content"])

@app.post("/agent/stream")
async def stream_agent_response(chat_input: ChatMessage):
    chat_id = chat_input.chat_id
    user_message = chat_input.message
    gemini_api_key = chat_input.gemini_api_key
    n8n_api_key = chat_input.n8n_api_key
    n8n_uri = chat_input.n8n_uri
    await load_chat_into_memory(chat_id)
    
    queue = Queue()
    cb_handler = CustomCallBackHandler(queue)
    config = RunnableConfig(callbacks=[cb_handler])
    
    async def generate_response():
        agent_response = ""
        
        try:
            fetch_existing_workflow = await wrapper_fetch_existing_workflow(n8n_uri,n8n_api_key)
            get_all_existing_workflows = await wrapper_get_all_existing_workflows(n8n_uri,n8n_api_key)
            post_workflow = await wrapper_post_worflow(n8n_uri,n8n_api_key)
            tools = [
                fetch_existing_workflow,
                get_all_existing_workflows,
                post_workflow,
                create_workflow_from_prompt,
                explain_workflow,  
                modify_workflow
            ] 
            agent_executor = await create_agent_executor(gemini_api_key,tools)
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
                    
                    elif data["type"] in ["thought", "observation", "final_answer_start", "final_answer_end"]:
                        yield f"data: {message}\n\n"
                    #"error",
                    elif data["type"] == "end":
                        yield f"data: {message}\n\n"
                        break
                
                except asyncio.TimeoutError:
                    if agent_task.done():
                        try:
                            agent_task.result()
                        except (InvalidArgument,ChatGoogleGenerativeAIError) as e:
                            yield f"data: {json.dumps({'type': 'invalid_api_key', 'content': 'Invalid Gemini API key. Please update your API keys.'})}\n\n"
                            return
                        except Exception as e:
                            yield f"data: {json.dumps({'type': 'error', 'content': f'Agent error: {str(e)}'})}\n\n"
                            return
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
                except (InvalidArgument, ChatGoogleGenerativeAIError) as e:
                    yield f"data: {json.dumps({'type': 'invalid_api_key', 'content': 'Invalid Gemini API key. Please update your API keys.'})}\n\n"
                    return
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Agent error: {str(e)}'})}\n\n"
                    return
            else:
                # Task is done, check if it completed successfully
                try:
                    final_result = agent_task.result()
                    if isinstance(final_result, dict) and 'output' in final_result and not agent_response:
                        agent_response = final_result['output']
                    elif isinstance(final_result, str) and not agent_response:
                        agent_response = final_result
                except (InvalidArgument, ChatGoogleGenerativeAIError) as e:
                    yield f"data: {json.dumps({'type': 'invalid_api_key', 'content': 'Invalid Gemini API key. Please update your API keys.'})}\n\n"
                    return
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Agent error: {str(e)}'})}\n\n"
                    return
            
            # Only save message if we have a valid response
            if agent_response:
                await save_message(chat_id,"user",user_message)
                await save_message(chat_id, "assistant", agent_response.strip())
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

@app.post("/validate-n8n-api-key")
async def validate_n8n_api_key(request:Request):
    response_dict = await request.json()
    n8nUrl = response_dict["n8nUrl"]
    n8nApiKey = response_dict["n8nApiKey"]
    try:
        n8n_validation_response = requests.get(f"{n8nUrl}/api/v1/workflows",
            headers={
                "accept": "application/json",
                "X-N8N-API-KEY": f"{n8nApiKey}"                         
        })
        if n8n_validation_response.status_code == 200:
            return {"success":True}
        elif n8n_validation_response.status_code == 401:
            return {"success":False,"message":"unauthorized"}
    except ConnectionError:
        return {"success":False,"message":"Connection Issue"}

@app.post("/validate-gemini-api-key")
async def validate_gemini_api_key(request:Request):
    response_dict = await request.json()
    geminiApiKey = response_dict["geminiApiKey"]
    try:
        response = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={geminiApiKey}")
        if response.status_code == 200:
            return {"success":True}
        elif response.status_code == 403:
            return {"success":False,"message":"Invalid or unauthorized API key"}
        elif response.status_code == 429:
            return {"success":False,"message":"Quota exceeded or rate limited"}
    except Exception as e:
        return {"success":False,"message":"Connection Issue"}

@app.post("/chat/new")
async def create_chat(request: Request):
    user_data = await get_user_from_token(request)
    title = "New Chat"
    
    new_chat_response = await create_new_chat(user_data["email"], title)
    if new_chat_response["success"]:
        return {"chat_id": new_chat_response["chat_id"], "title": title}
    raise HTTPException(status_code=500,detail="Internal Server Error")

@app.get("/chat/list")
async def list_chats(request: Request):
    user_data = await get_user_from_token(request)
    chats = await get_user_chats(user_data["email"])
    return {"chats": chats}

@app.get("/chat/recent")
async def get_recent_chat(request: Request):
    user_data = await get_user_from_token(request)
    chat_id = await get_most_recent_chat(user_data["email"])
    
    if not chat_id:
        new_chat_response = await create_new_chat(user_data["email"], "New Chat")
        if new_chat_response["success"]:
            chat_id = new_chat_response["chat_id"]
        else:
            raise HTTPException(status_code=500, detail="Failed to create new chat")
    
    return {"chat_id": chat_id}

@app.get("/chat/{chat_id}/messages")
async def get_chat_history_from_db(chat_id: str):
    messages = await get_chat_messages(chat_id)
    
    await update_chat_access(chat_id)
    
    return {"messages": messages}

@app.put("/chat/{chat_id}/title")
async def update_chat_title_endpoint(chat_id: str, request: Request):
    body = await request.json()
    title = body["title"]
    await update_chat_title(chat_id, title)
    return {"success": True}

@app.delete("/chat/{chat_id}")
async def delete_chat_endpoint(chat_id: str):
    await delete_chat(chat_id)
    return {"success": True}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) 
    uvicorn.run("app:app", host="0.0.0.0", port=port)