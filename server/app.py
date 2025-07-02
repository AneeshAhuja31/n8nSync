from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from workflow_tools import *
from prompt_templates import system_prompt_template
from langchain.agents import initialize_agent
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY,model="gemini-2.5-flash")

tools = []

agent = initialize_agent(
    llm = llm,
    tools=tools,
    prompt=system_prompt_template,
    
)


@app.get("/")
async def root():
    return {"message":"n8n Agentic Workflow Builder"}




