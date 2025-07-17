from langchain_core.tools import Tool
import requests
from typing import Dict, Any
from tool_descriptions import fetch_exisiting_workflow_description, get_all_exisiting_workflows_description, post_workflow_description,create_workflow_from_prompt_description, explain_workflow_description, modify_workflow_description
from prompt_templates import creation_prompt_template, explaination_prompt_template, modification_prompt_template
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json
import ast
from api_key_manager import APIKeyManager
load_dotenv()

key_manager = APIKeyManager()

llm = ChatGoogleGenerativeAI(
            api_key=key_manager.get_next_key(),
            model="gemini-2.5-flash",
            temperature=0.4,
            #convert_system_message_to_human=True
        )

def remove_keys(obj, keys_to_remove):
    if isinstance(obj, dict):
        return {
            k: remove_keys(v, keys_to_remove)
            for k, v in obj.items()
            if k not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [remove_keys(item, keys_to_remove) for item in obj]
    else:
        return obj
    
async def wrapper_fetch_existing_workflow(n8n_uri:str,api_key: str) -> Tool:
    def _fetch_existing_workflow(workflow_id: str) -> Dict[str, Any]:
        try:
            response = requests.get(f"{n8n_uri}/api/v1/workflows/{workflow_id}", headers={
                "accept": "application/json",
                "X-N8N-API-KEY": api_key
            })
            if response.status_code == 200:
                data = response.json()
                keys_to_remove = [
                    "active", "id", "createdAt", "updatedAt", "isArchived", "staticData",
                    "meta", "pinData", "versionId", "triggerCount", "shared", "tags"
                ]
                cleaned_data = remove_keys(data,keys_to_remove)
                return cleaned_data
            return {"success": False, "error": f"Error in retrieving workflow with id: {workflow_id}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    return Tool(
        name="fetch_existing_workflow",
        description=fetch_exisiting_workflow_description,
        func=_fetch_existing_workflow
    )

async def wrapper_get_all_existing_workflows(n8n_uri:str,api_key:str) ->Tool:
    def _get_all_exisiting_workflows() -> Dict[str, Any]:
        try:
            response = requests.get(f"{n8n_uri}/api/v1/workflows", headers={
                "accept": "application/json",
                "X-N8N-API-KEY": f"{api_key}"
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
        except ConnectionError as e:
            return {"success":False,"error":f"n8n instance not running, tell user to first start the n8n instance"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    return Tool(
        name="get_all_exisiting_workflows",
        description=get_all_exisiting_workflows_description,
        func=lambda _: _get_all_exisiting_workflows()
    )

async def wrapper_post_worflow(n8n_uri:str,api_key:str) -> Tool:
    def _post_workflow(workflow_json: str)->Dict[str,Any]:
        try:
            if isinstance(workflow_json, str):
                try:
                    
                    try:
                        workflow_json = json.loads(workflow_json)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try ast.literal_eval
                        workflow_json = workflow_json.replace('\\"', '"')
                        workflow_json = ast.literal_eval(workflow_json)
                        
                except (ValueError, SyntaxError, json.JSONDecodeError) as e:
                    return {"success": False, "error": f"Invalid input format: {e}"} 
                
            else:
                return {"success": False, "error": "Input must be a string in format of a dictionary"}
            
            if not workflow_json:
                return {"success": False, "error": "Workflow_json is required"}
            
            # Remove problematic keys before posting
            keys_to_remove = [
                "active", "id", "createdAt", "updatedAt", "isArchived", "staticData",
                "meta", "pinData", "versionId", "triggerCount", "shared", "tags"
            ]
            
            # Clean the workflow JSON
            cleaned_workflow = remove_keys(workflow_json, keys_to_remove)
            
            response = requests.post(f"{n8n_uri}/api/v1/workflows",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "X-N8N-API-KEY": f"{api_key}"
                    },
                    json=cleaned_workflow
            )
            
            if response.status_code == 200:
                response_json = response.json()
                workflow_name = response_json.get("name", "Unknown")
                return {
                    "success": True,
                    "message": f"Workflow JSON: {workflow_name} posted successfully!",
                    "workflow_id": response_json.get("id")
                }
            else:
                try:
                    response_json = response.json()
                    error_message = response_json.get("message", "Unknown error")
                except:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                    
                if response.status_code == 400:
                    if "active is read-only" in error_message:
                        return {
                            "success": False,
                            "message": "Remove 'active' key from workflow JSON and retry",
                            "status_code": response.status_code
                        }
                    elif "id is read-only" in error_message:
                        return {
                            "success": False,
                            "message": "Remove 'id' key from workflow JSON and retry",
                            "status_code": response.status_code
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Workflow JSON has errors: {error_message}",
                            "status_code": response.status_code
                        }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "message": "Unauthorized access - check API key"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Request failed: {error_message}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            return {"success": False, "error": f"Post Request to post workflow failed: {str(e)}"}
            
    return Tool(
        name="post_workflow",
        description=post_workflow_description,
        func=_post_workflow
    )
        
def _create_workflow_from_prompt(prompt: str) -> Dict[str, Any]:
    try:
        full_prompt = creation_prompt_template.replace('[[USER_PROMPT]]', prompt)

        
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

        try:
            parsed_json = json.loads(response_text)
            return parsed_json
        except json.JSONDecodeError as e:
            return response_text
            #return {"success": False, "error": f"Failed to parse JSON: {e}\nRaw output:\n{response_text}"}
    except Exception as e:
        return {"success": False, "error": f"Workflow creation failed: {str(e)}"}

def _explain_workflow(workflow_json: Dict[str, Any]) -> Dict[str, Any]:
    try:
        explaination_prompt_string = explaination_prompt_template.format(
            workflow_json=json.dumps(workflow_json, indent=2)
        )
        response_text = ""
        
        for chunk in llm.stream(explaination_prompt_string.content):
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

def _modify_workflow(input_dict: str) -> Dict[str, Any]:
    """Extract workflow_json and custom_changes from input"""
    try:
        if not isinstance(input_dict, str):
            return {"success": False, "error": "Input must be a dictionary or JSON string"}
        
        if not ('"workflow_json"' or "'workflow_json'") or not ('"custom_changes"' or "'custom_changes'"):
            return {"success": False, "error": "Both workflow_json and custom_changes are required keys in the input"}
        
        
        formatted_message = modification_prompt_template.format(
            existing_workflow_json_with_custom_changes = input_dict
        )
        
        response_text = ""
        
        #stream formatted message content
        for chunk in llm.stream(formatted_message.content):
            if chunk.content:
                response_text += chunk.content
        
        response_text = response_text.strip()

        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").strip("`\n ")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip("`\n ")
        
        return {
            "success": True,
            "modified_workflow": response_text
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error modifying workflow: {str(e)}"
        }

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