from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.agents import AgentAction,AgentFinish
from asyncio import Queue
import json

class CustomCallBackHandler(AsyncCallbackHandler):
    def __init__(self,queue:Queue):
        self.queue = queue
        self.is_final_answer = False

    async def on_agent_action(self, action:AgentAction,**kwargs):
        await self.queue.put(json.dumps({
            "type":"thought",
            "content":f"Using tool: {action.tool}",
            "tool":action.tool,
            "input":action.tool_input
        }))
    
    async def on_agent_finish(self, finish:AgentFinish,**kwargs):
        self.is_final_answer = True
        await self.queue.put(json.dumps({
            "type":"final_answer_start",
            "content":""
        }))

    async def on_tool_start(self, serialized, input_str,**kwargs):
        tool_name = serialized['name']
        await self.queue.put(json.dumps({
            "type":"thought",
            "content":f"Executing {tool_name}...",
            "tool":tool_name,
            "input":input_str
        }))
    
    async def on_tool_end(self, output,**kwargs):
        await self.queue.put(json.dumps({
            "type":"observation",
            "content":str(output)
        }))
    
    async def on_llm_new_token(self, token,**kwargs): 
        if self.is_final_answer:
            await self.queue.put(json.dumps({
                "type":"token",
                "content":token
            })) 
        else:
            pass #during thinking phase,dont stream tokens
    
    async def on_tool_error(self, error:BaseException,**kwargs):
        await self.queue.put(json.dumps({
            "type":"error",
            "content":f"Tool Error: {str(error)}"
        }))
    
    async def on_chain_error(self, error:BaseException,**kwargs):
        await self.queue.put(json.dumps({
            "type":"error",
            "content":f"LLM Error: {str(error)}"
        }))
    
    async def on_llm_error(self, error: BaseException, **kwargs):
        await self.queue.put(json.dumps({
            "type": "error",
            "content": f"LLM Error: {str(error)}"
        }))
        
    async def on_chain_end(self, outputs, **kwargs):
        if self.is_final_answer:
            await self.queue.put(json.dumps({
                "type": "final_answer_end",
                "content": ""
            }))
            await self.queue.put(json.dumps({
                "type": "end",
                "content": ""
            }))
        self.is_final_answer = False
    
