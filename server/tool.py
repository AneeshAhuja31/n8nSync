from langchain.tools import tool
import requests

@tool
async def fetch_exisiting_workflow(n8n_api_key,workflow_id,uri="localhost:5678"):
    response = requests.get(f"http://{uri}/api/v1/workflows/{workflow_id}",headers={
        "accept":"application/json",
        "X-N8N-API-KEY":f"{n8n_api_key}"
    })
    if response.status_code == 200:
        return response
    return f"Error in retrieving workflow with id: {workflow_id}"

@tool
async def get_all_exisiting_workflows(n8n_api_key,uri="localhost:5678"):
    response = requests.get(f"http://{uri}/api/v1/workflows",headers={
        "accept":"application/json",
        "X-N8N-API-KEY":f"{n8n_api_key}"
    })
    if response.status_code == 200:
        response_data = response.json()
        complete_worflow_list = response_data['data']
        if len(complete_worflow_list) == 0:
            return "No workflows yet!"
        workflow_name_w_id_list = [
            {"name": item["name"], "id": item["id"], "active": item["active"]}
            for item in complete_worflow_list
        ]
        return workflow_name_w_id_list
    else: 
        return "Error in retrieving existing workflows"
        
        
        
    

