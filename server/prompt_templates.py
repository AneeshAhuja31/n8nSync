from langchain_core.prompts import SystemMessagePromptTemplate
from string import Template
system_prompt_template = SystemMessagePromptTemplate.from_template("""

""")

creation_prompt_template = Template("""
    You are an expert in building automation workflows using n8n.
    Your goal is to generate a complete and valid n8n workflow JSON based on the user's request.

    **n8n Workflow Structure Guidelines:**

    * **Overall JSON Object:**
        ```json
        {
        "name": "Workflow Name",
        "nodes": [ /* Array of node objects */ ],
        "connections": { /* Object defining node connections */ },
        "settings": { "executionOrder": "v1" },
        "active": false
        }
        ```
    * **Node Object Structure:**
        * `"name"`: A descriptive string for the node (e.g., "Schedule Weekly", "Get Subscribers").
        * `"type"`: The full n8n node type string (e.g., "n8n-nodes-base.cron", "n8n-nodes-base.googleSheets", "n8n-nodes-base.gmail", "n8n-nodes-base.set", "n8n-nodes-base.githubTrigger", "n8n-nodes-base.if", "n8n-nodes-base.slack", "n8n-nodes-base.webhook", "n8n-nodes-base.function", "n8n-nodes-base.httpRequest", "n8n-nodes-base.mysql", "n8n-nodes-base.splitInBatches", "n8n-nodes-base.emailSend", "n8n-nodes-base.stripe").
        * `"typeVersion"`: Integer, typically 1 or 2.
        * `"position"`: `[x, y]` array, for visual layout. Start with `[240, 300]` for the first node and increment `x` by `220` for subsequent nodes in a linear flow, adjusting `y` for branching.
        * `"parameters"`: A dictionary specific to the node type and its configuration.
            * **Expressions:** Use `={{...}}` for dynamic values, referencing previous node outputs (e.g., `={{$node['NodeName'].json['field']}}`) or built-in functions (e.g., `{{DateTime.now().toFormat('MMM dd,YYYY')}}`).
            * **Credential Fields:** If a node requires credentials (e.g., `googleSheetsApi`, `gmailApi`, `clearbitApi`, `openWeatherApi`, `slackApi`, `stripeApi`, `mysql`) include a `"credentials"` object with the appropriate credential type and ID (use placeholder `"[YOUR_CREDENTIAL_ID]"`).
                Example: `"credentials": { "gmailApi": "[YOUR_CREDENTIAL_ID]" }`
            * **Function Node `functionCode`**: This should contain valid JavaScript. Remember to escape newlines as `\\n`.
        * `"id"`: A unique identifier (UUID recommended, but a string can also be used). You can generate simple sequential IDs for the examples or omit them if the LLM can infer.

    * **Connections Object Structure:**
        * Keys are node names (from the `"name"` field of the source node).
        * Values are objects, often with a `"main"` key containing an array of arrays, each inner array specifying a connection target.
        * Each target connection is an object: `{"node": "Target Node Name", "type": "main", "index": 0}`.
        * For IF nodes, the `true` branch is `index: 0` and the `false` branch is `index: 1`.

    * **Workflow Settings:** Always include `"settings": { "executionOrder": "v1" }` and `"active": false`.

    **IMPORTANT:**
    * **Generate ONLY the JSON object.** Do not include any explanatory text, markdown outside the JSON, or conversational elements.
    * **Ensure the JSON is syntactically correct and complete.**
    * **Use placeholder values for API keys and IDs** like "YOUR_API_KEY", "[YOUR_CREDENTIAL_ID]", "1ABC123_your_sheet_id", "your-username", "your-repo" where appropriate, to indicate user configuration is needed.
    * **Node positions should increment logically** to represent a clear flow.

    Now, generate an n8n workflow JSON based on the following user prompt:
    ${prompt}
    """
    )