fetch_exisiting_workflow_description="""
    Fetch a specific workflow from an n8n instance by its workflow ID.
    
    IMPORTANT: The input of this tool is only a string which is the alphanumeric identifer of workflow.
    DO NOT PASS A Dict as input.

    Use this tool when:
    - User wants to view details of a specific workflow
    - User provides a workflow ID and wants to see its configuration
    - You need to retrieve a workflow before explaining or modifying it
    - User asks about a particular workflow by ID
    
    Input Parameters:
    - workflow_id (str): Required. This must be alphanumeric. The unique identifier of the workflow to retrieve
    
    Example usage scenarios:
    - "Show me workflow with ID abc123"
    - "I want to see the details of workflow xyz456"
    - "Can you fetch workflow 789 from my n8n instance?"
"""

get_all_exisiting_workflows_description = """
    Get a list of all workflows from an n8n instance with basic information.
    
    Use this tool when:
    - User wants to see all available workflows
    - User asks "what workflows do I have?"
    - You need to help user find a workflow by name
    - User wants to browse their existing workflows
    - User doesn't know the specific workflow ID
    
    Example usage scenarios:
    - "Show me all my workflows"
    - "List all workflows in my n8n instance"
    - "What workflows do I have?"
    - "I need to find a workflow but don't know the ID"
    """

create_workflow_from_prompt_description = """
    Generate a complete n8n workflow JSON from a natural language description.
    
    Use this tool when:
    - User wants to create a new workflow from scratch
    - User describes what they want to automate
    - User provides requirements for a new automation
    - User says "create a workflow that..." or "build an automation for..."
    
    Input Parameters:
    - prompt (str): Required. Natural language description of the desired workflow functionality
    
    Important Notes:
    - The returned workflow will have placeholder credential IDs that need to be configured
    - Workflow is created as inactive by default
    - Generated JSON is ready for n8n import
    - May raise ValueError if JSON parsing fails
    
    Example usage scenarios:
    - "Create a workflow that sends email notifications when new data appears in Google Sheets"
    - "I want to automate posting to Slack when GitHub issues are created"
    - "Build a workflow that processes CSV files and sends reports"
    - "Make an automation that monitors website changes and alerts me"
    """

explain_workflow_description = """
    Analyze a workflow JSON and provide a human-readable explanation of its functionality.
    
    Use this tool when:
    - User wants to understand what a workflow does
    - User asks "explain this workflow" or "what does this workflow do?"
    - User needs help understanding complex workflow logic
    - User wants documentation for an existing workflow
    - After fetching a workflow and user wants explanation
    
    Input Parameters:
    - workflow_json (Dict[str, Any]): Required. Complete n8n workflow JSON object to analyze
    
    The explanation includes:
    - Main purpose of the workflow
    - How it's triggered
    - Step-by-step process description
    - Expected outputs/actions
    - Potential issues or improvements
    
    Example usage scenarios:
    - "Explain what this workflow does"
    - "I don't understand this automation, can you help?"
    - "What's the purpose of workflow abc123?"
    - "Help me understand the logic of this workflow"
    """

modify_workflow_description = """
    IMPORTANT: The input of this tool which is input_dict will be a string in the format (again format not datatype) of a dictionary (in which both keys and values are strings) with keys:
        workflow_json : which is the workflow json to be modified, it is to be in proper dictionary format.
        custom_changes : this is the custom changes the user wants on the workflow json.
    Modify an existing workflow based on specific change requirements.
    
    Use this tool when:
    - User wants to modify an existing workflow
    - User says "change this workflow to..." or "add/remove/update..."
    - User needs to adapt a workflow for new requirements
    - User wants to enhance or fix an existing automation
    
    Input Parameters:
    - input_dict: (str): Required. Where input_dict will be a string in format of a dictionary.
    Format of input_dict: Dictionary with workflow_json key and custom_changes key, where workflow_json value is the workflow json (Dict) to be modified, and custom_changes value is the (str) prompt which specifies the modification. 
    
    The modified workflow:
    - Maintains existing structure and format
    - Incorporates requested changes  
    - Preserves valid node connections
    - Returns complete, valid n8n workflow JSON
    
    Example usage scenarios:
    - "Add a Slack notification to this workflow"
    - "Change the schedule from daily to weekly"
    - "Remove the email step and add a database update"
    - "Modify the condition logic in this workflow"
    - "Add error handling to this automation"
    """