from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.agents import AgentAction,AgentFinish
from asyncio import Queue

class CustomCallBackHandler(AsyncCallbackHandler):
    def __init__(self,queue:Queue):
        self.queue = queue
    async def on_agent_action(self, action:AgentAction,**kwargs):
        await self.queue.put(f"ACTION: {action}")
    
    async def on_agent_finish(self, finish:AgentFinish,**kwargs):
        await self.queue.put(f"FINAL ANSWER: {finish.return_values['output']}")
        await self.queue.put(f"[END]")

    async def on_tool_start(self, serialized, input_str,**kwargs):
        tool = serialized['name']
        await self.queue.put(f"ACTION: {tool}\n{input_str}")
    
    async def on_tool_end(self, output,**kwargs):
        await self.queue.put(f"OBSERVATION: {output}")
    
    async def on_llm_new_token(self, token,**kwargs): # token by token streaming/to get responses as llm generates them
        await self.queue.put(f"TOKEN: {token}") #TOKEN prefix to be removed in the frontend
    
    async def on_tool_error(self, error:BaseException,**kwargs):
        await self.queue.put(f"TOOL ERROR: {str(error)}")
    
    async def on_chain_error(self, error:BaseException,**kwargs):
        await self.queue.put(f"CHAIN ERROR: {error}")
    
    async def on_llm_error(self, error:BaseException,**kwargs):
        await self.queue.put(f"LLM ERROR: {error}")
    
