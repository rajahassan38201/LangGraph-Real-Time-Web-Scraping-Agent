import json
import uvicorn
from typing import TypedDict, Annotated, Optional
from uuid import uuid4
 
from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
 
# Load API keys from .env file
load_dotenv() 

# Initialize memory saver for checkpointing
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize the search tool
search_tool = TavilySearchResults(
    max_results=4,
)
tools = [search_tool]

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools=tools)

async def model(state: State):
    """LLM node."""
    result = await llm_with_tools.ainvoke(state["messages"])
    return {
        "messages": [result], 
    }

async def tools_router(state: State):
    """Router node to check for tool calls."""
    last_message = state["messages"][-1]
    if(hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0):
        return "tool_node"
    else: 
        return END
    
async def tool_node(state):
    """Custom tool node that handles tool calls from the LLM."""
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        if tool_name == "tavily_search_results_json":
            search_results = await search_tool.ainvoke(tool_args)
            tool_message = ToolMessage(
                content=str(search_results),
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
    
    return {"messages": tool_messages}

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("model", model)
graph_builder.add_node("tool_node", tool_node)
graph_builder.set_entry_point("model")
graph_builder.add_conditional_edges("model", tools_router)
graph_builder.add_edge("tool_node", "model")

graph = graph_builder.compile(checkpointer=memory)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
    expose_headers=["Content-Type"], 
)

async def generate_chat_responses(message: str, checkpoint_id: Optional[str] = None):
    """
    Generates and streams chat responses using Server-Sent Events (SSE).
    """
    is_new_conversation = checkpoint_id is None
    
    if is_new_conversation:
        new_checkpoint_id = str(uuid4())
        config = {"configurable": {"thread_id": new_checkpoint_id}}
        
        # Send the new checkpoint ID first
        yield f"data: {json.dumps({'type': 'checkpoint', 'checkpoint_id': new_checkpoint_id})}\n\n"
    else:
        config = {"configurable": {"thread_id": checkpoint_id}}

    # Start streaming events from the graph
    events = graph.astream_events(
        {"messages": [HumanMessage(content=message)]},
        version="v2",
        config=config
    )

    async for event in events:
        event_type = event["event"]
        
        if event_type == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                # Stream content chunks
                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
                
        elif event_type == "on_chat_model_end":
            # Check if a tool call was made
            tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
            search_calls = [call for call in tool_calls if call["name"] == "tavily_search_results_json"]
            
            if search_calls:
                # Signal that a search is starting
                search_query = search_calls[0]["args"].get("query", "")
                yield f"data: {json.dumps({'type': 'search_start', 'query': search_query})}\n\n"
                
        elif event_type == "on_tool_end" and event["name"] == "tavily_search_results_json":
            # Search completed, send results
            output = event["data"]["output"]
            urls = []
            if isinstance(output, list):
                urls = [item["url"] for item in output if isinstance(item, dict) and "url" in item]
            
            yield f"data: {json.dumps({'type': 'search_results', 'urls': urls})}\n\n"

    # Send an end event when the stream is finished
    yield f"data: {json.dumps({'type': 'end'})}\n\n"

@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    """
    FastAPI endpoint to handle streaming chat responses.
    """
    return StreamingResponse(
        generate_chat_responses(message, checkpoint_id), 
        media_type="text/event-stream"
    )

# Run the app
if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)










