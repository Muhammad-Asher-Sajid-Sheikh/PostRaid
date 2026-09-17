import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools.tool import rag_tool, generate_image, update_image, delete_image

load_dotenv()

# 1. Define State
class AgentState(TypedDict):
    # add_messages automatically handles appending AI and Tool messages to history
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Register tools
tools_list = [rag_tool, generate_image, update_image, delete_image]
tool_node = ToolNode(tools_list)

# 3. Model setup with tool binding
llm = ChatGoogleGenerativeAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    temperature=0.3
)
llm_with_tools = llm.bind_tools(tools_list)

# Node 1: Agent decision step
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 4. Build the StateGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# Add Edges & Control Flow
workflow.add_edge(START, "agent")
# Conditional routing: if LLM output includes tool_calls -> go to "tools", else -> END
workflow.add_conditional_edges("agent", tools_condition)
# Cyclic loop: return output from tool executions back to the agent
workflow.add_edge("tools", "agent")

# Compile the execution graph
app = workflow.compile()


def call_agent(data: str) -> str:
    """
    Main entry point to run the agent flow and get the text output.
    """
    system_instruction = "You are an AI assistant responsible for using tools to complete user requests."
    user_prompt = f"Select and call the correct tools to perform this task:\n{data}"

    initial_messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_prompt)
    ]

    # Run the graph until completion
    final_state = app.invoke({"messages": initial_messages})

    # Return content from the final message in state
    return final_state["messages"][-1].content