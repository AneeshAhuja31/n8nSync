from langchain_core.tools import Tool
import requests
from typing import Dict, Any, List
from tool_descriptions import fetch_exisiting_workflow_description, get_all_exisiting_workflows_description, create_workflow_from_prompt_description, explain_workflow_description, modify_workflow_description
from prompt_templates import creation_prompt_template, explaination_prompt_template, modification_prompt_template
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json
from string import Template

load_dotenv()

gemini_api_key_workflow_generation = os.getenv("GEMINI_API_KEY_WORKFLOW_GENERATION")
n8n_api_key = os.getenv("N8N_API_KEY")

def _fetch_exisiting_workflow(workflow_id: str, uri: str = "localhost:5678") -> Dict[str, Any]:
    try:
        response = requests.get(f"http://{uri}/api/v1/workflows/{workflow_id}", headers={
            "accept": "application/json",
            "X-N8N-API-KEY": f"{n8n_api_key}"
        })
        if response.status_code == 200:
            return {"success": True, "workflow": response.json()}
        return {"success": False, "error": f"Error in retrieving workflow with id: {workflow_id}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

def _get_all_exisiting_workflows(uri: str = "localhost:5678") -> Dict[str, Any]:
    try:
        response = requests.get(f"http://{uri}/api/v1/workflows", headers={
            "accept": "application/json",
            "X-N8N-API-KEY": f"{n8n_api_key}"
        })
        if response.status_code == 200:
            response_data = response.json()
            complete_workflow_list = response_data['data']
            if len(complete_workflow_list) == 0:
                return {"success": True, "workflow_list": []}
            workflow_name_w_id_list = [
                {"name": item["name"], "id": item["id"], "active": item["active"]}
                for item in complete_workflow_list
            ]
            return {
                "success": True,
                "workflow_list": workflow_name_w_id_list
            }
        else: 
            return {"success": False, "error": "Error in retrieving existing workflows", "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

def _create_workflow_from_prompt(prompt: str) -> Dict[str, Any]:
    try:
        full_prompt = creation_prompt_template.replace('[[USER_PROMPT]]', prompt)

        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.4,
            convert_system_message_to_human=True
        )
        response_text = ""
        
        for chunk in llm.stream(full_prompt):
            if chunk.content:
                response_text += chunk.content
        
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").strip("`\n ")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip("`\n ")
        response_text=response_text.replace("'",'"')
        print("//////////////////")
        print(response_text)
        print("/////////////////////")
        try:
            parsed_json = json.loads(response_text)
            return parsed_json
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse JSON: {e}\nRaw output:\n{response_text}"}
    except Exception as e:
        return {"success": False, "error": f"Workflow creation failed: {str(e)}"}

def _explain_workflow(workflow_json: Dict[str, Any]) -> Dict[str, Any]:
    try:
        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.3,
            convert_system_message_to_human=True
        )
        messages = explaination_prompt_template.format(
            workflow_json=json.dumps(workflow_json, indent=2)
        )
        response_text = ""
        
        for chunk in llm.stream(messages):
            if chunk.content:
                response_text += chunk.content
        
        return {
            "success": True,
            "explanation": response_text.strip()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error explaining workflow: {str(e)}"
        }

def _modify_workflow(workflow_json: Dict[str, Any], custom_changes: str) -> Dict[str, Any]:
    """Modify an existing workflow"""
    try:
        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.4,
            convert_system_message_to_human=True
        )
        modification_prompt = modification_prompt_template.format(
            existing_workflow_json=json.dumps(workflow_json, indent=2),
            custom_changes=custom_changes
        )
        response_text = ""
        
        for chunk in llm.stream(modification_prompt):
            if chunk.content:
                response_text += chunk.content
        
        response_text = response_text.strip()

        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").strip("`\n ")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip("`\n ")
        
        try:
            modified_workflow = json.loads(response_text)
            return {
                "success": True,
                "modified_workflow": modified_workflow
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse modified workflow JSON: {e}\nRaw output:\n{response_text}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error modifying workflow: {str(e)}"
        }

fetch_existing_workflow = Tool(
    name="fetch_existing_workflow",
    description=fetch_exisiting_workflow_description,
    func=_fetch_exisiting_workflow
)

get_all_existing_workflows = Tool(
    name="get_all_existing_workflows", 
    description=get_all_exisiting_workflows_description,
    func=_get_all_exisiting_workflows
)

create_workflow_from_prompt = Tool(
    name="create_workflow_from_prompt",
    description=create_workflow_from_prompt_description,
    func=_create_workflow_from_prompt
)

explain_workflow = Tool(
    name="explain_workflow",
    description=explain_workflow_description,
    func=_explain_workflow
)

modify_workflow = Tool(
    name="modify_workflow", 
    description=modify_workflow_description,
    func=_modify_workflow
)