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
load_dotenv()

gemini_api_key_workflow_generation = os.getenv("GEMINI_API_KEY_WORKFLOW_GENERATION")

async def wrapper_fetch_existing_workflow(api_key: str) -> Tool:
    def _fetch_existing_workflow(workflow_id: str) -> Dict[str, Any]:
        try:
            response = requests.get(f"http://localhost:5678/api/v1/workflows/{workflow_id}", headers={
                "accept": "application/json",
                "X-N8N-API-KEY": api_key
            })
            if response.status_code == 200:
                return str(response.json())
            return {"success": False, "error": f"Error in retrieving workflow with id: {workflow_id}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    return Tool(
        name="fetch_existing_workflow",
        description=fetch_exisiting_workflow_description,
        func=_fetch_existing_workflow
    )

async def wrapper_get_all_existing_workflows(api_key:str) ->Tool:
    def _get_all_exisiting_workflows() -> Dict[str, Any]:
        try:
            response = requests.get(f"http://localhost:5678/api/v1/workflows", headers={
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
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    return Tool(
        name="get_all_exisiting_workflows",
        description=get_all_exisiting_workflows_description,
        func=lambda _: _get_all_exisiting_workflows()
    )
async def wrapper_post_worflow(api_key:str) -> Tool:
    def _post_workflow(workflow_json: str)->Dict[str,Any]:
        try:
            if isinstance(workflow_json, str):
                try:
                    workflow_json = ast.literal_eval(workflow_json)
                except (ValueError, SyntaxError) as e:
                    return {"success": False, "error": f"Invalid input format: {e}"} 
                
            else:
                return {"success": False, "error": "Input must be a string in format of a dictionary"}
            
            if not workflow_json:
                return {"success": False, "error": "Workflow_json is required"}
            
            response = requests.post(f"http://localhost:5678/api/v1/workflows",
                    headers={
                        "accept": "application/json",
                        "X-N8N-API-KEY": f"{api_key}"
                    },
                    json=workflow_json
            )
            response_json = response.json()
            if response.status_code == 200:
                workflow_name = response_json.get("name")
                return {
                    "success":True,
                    "message": f"Workflow JSON: {workflow_name} , posted successfully!"
                }
            elif response.status_code == 400: #invalid workflow_json
                if response_json["message"] == "request/body/active is read-only":
                    return {
                        "success":False,
                        "message":"Remove active set to true/false key value pair from the workflow json and retry",
                        "status_code":response.status_code
                    }
                wrong_syntax_message = response_json["message"]
                return {
                    "success":False,
                    "message":f"Workflow JSON has errors: {wrong_syntax_message}",
                    "status_code":response.status_code
                }
            elif response.status_code == 401:
                return {
                    "success":False,
                    "message":"Unauthorized access"
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

        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.4,
            #convert_system_message_to_human=True
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
            #convert_system_message_to_human=True
        )
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
        if isinstance(input_dict, str):
            try:
                parsed_input = ast.literal_eval(input_dict)
                workflow_json = parsed_input.get("workflow_json", {})
                custom_changes = parsed_input.get("custom_changes", "")
            except (ValueError, SyntaxError) as e:
                return {"success": False, "error": f"Invalid input format: {e}"} 
            
        else:
            return {"success": False, "error": "Input must be a dictionary or JSON string"}
        
        if not workflow_json or not custom_changes:
            return {"success": False, "error": "Both workflow_json and custom_changes are required"}
        
        llm = ChatGoogleGenerativeAI(
            api_key=gemini_api_key_workflow_generation,
            model="gemini-2.5-flash",
            temperature=0.4
        )
        
        # Format the message properly as a string
        formatted_message = modification_prompt_template.format(
            existing_workflow_json=json.dumps(workflow_json, indent=2),
            custom_changes=custom_changes
        )
        
        response_text = ""
        
        # Stream the formatted message content
        for chunk in llm.stream(formatted_message.content):
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