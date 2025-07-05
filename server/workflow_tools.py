from langchain.tools import tool
import requests
from typing import Dict,Any,List
from tool_descriptions import fetch_exisiting_workflow_description,get_all_exisiting_workflows_description,create_workflow_from_prompt_description,explain_workflow_description,modify_workflow_description
from prompt_templates import creation_prompt_template,explaination_prompt_template,modification_prompt_template
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json
load_dotenv()

gemini_api_key_workflow_generation = os.getenv("GEMINI_API_KEY_WORKFLOW_GENERATION")
n8n_api_key = os.getenv("N8N_API_KEY")

@tool(description=fetch_exisiting_workflow_description)
async def fetch_exisiting_workflow(workflow_id:str,uri:str="localhost:5678") -> str:
    response = requests.get(f"http://{uri}/api/v1/workflows/{workflow_id}",headers={
        "accept":"application/json",
        "X-N8N-API-KEY":f"{n8n_api_key}"
    })
    if response.status_code == 200:
        return json.dumps({"success":True,"workflow":response.json()})
    return json.dumps({"success":False,"error":f"Error in retrieving workflow with id: {workflow_id}"})

@tool(description=get_all_exisiting_workflows_description)
async def get_all_exisiting_workflows(uri:str="localhost:5678") -> str:
    response = requests.get(f"http://{uri}/api/v1/workflows",headers={
        "accept":"application/json",
        "X-N8N-API-KEY":f"{n8n_api_key}"
    })
    if response.status_code == 200:
        response_data = response.json()
        complete_worflow_list = response_data['data']
        if len(complete_worflow_list) == 0:
            return []
        workflow_name_w_id_list = [
            {"name": item["name"], "id": item["id"], "active": item["active"]}
            for item in complete_worflow_list
        ]
        return json.dumps({
            "success":True,
            "workflow":workflow_name_w_id_list
        })
    else: 
        return json.dumps({"success":False,"error":"Error in retrieving existing workflows","status_code":response.status_code})


@tool(description=create_workflow_from_prompt_description)
async def create_workflow_from_prompt(prompt:str) -> str:
    full_prompt = creation_prompt_template.replace("{{ prompt }}", prompt)
    
    llm = ChatGoogleGenerativeAI(
        api_key=gemini_api_key_workflow_generation,
        model="gemini-2.5-flash",
        temperature=0.4,
        convert_system_message_to_human=True
    )
    response_text = ""
    async for chunk in llm.astream(full_prompt):
        if chunk.content:
            response_text += chunk.content
    
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text.replace("```json", "").strip("`\n ")
    elif response_text.startswith("```"):
        response_text = response_text.replace("```", "").strip("`\n ")

    # Parse final JSON
    try:
        parsed_json = json.loads(response_text)
        return json.dumps(parsed_json)
    except json.JSONDecodeError as e:
        raise json.dumps(ValueError(f"Failed to parse JSON: {e}\nRaw output:\n{response_text}"))

@tool(description=explain_workflow_description)
async def explain_workflow(workflow_json:Dict[str,Any]) -> str:
    try:
        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.3,
            convert_system_message_to_human=True
        )
        messages = explaination_prompt_template.format_messages(
            workflow_json = json.dumps(workflow_json,indent=2)
        )
        response_text = ""
        async for chunk in llm.astream(messages):
            if chunk.content:
                response_text += chunk.content
        
        return json.dumps({
            "success": True,
            "explanation": response_text.strip()
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error explaining workflow: {str(e)}"
        })
    
@tool(description=modify_workflow_description)
async def modify_workflow(workflow_json:Dict[str,Any],custom_changes:str)->str:
    try:
        llm = ChatGoogleGenerativeAI(
                api_key=gemini_api_key_workflow_generation,
                model="gemini-2.5-flash",
                temperature=0.4,
                convert_system_message_to_human=True
            )
        modification_prompt = modification_prompt_template.format_messages(
            existing_workflow_json = json.dumps(workflow_json,indent=2),
            custom_changes = custom_changes
        )
        response_text = ""
        async for chunk in llm.astream(modification_prompt):
            if chunk.content:
                response_text += chunk.content
        response_text = response_text.strip()

        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").strip("`\n ")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip("`\n ")
        
        try:
            modified_workflow = json.loads(response_text)
            return json.dumps({
                "success": True,
                "modified_workflow": modified_workflow
            })
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Failed to parse modified workflow JSON: {e}\nRaw output:\n{response_text}"
            })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error modifying workflow: {str(e)}"
        })
