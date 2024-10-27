from langchain_core.tools import tool
from langchain_dartmouth.llms import ChatDartmouth
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatDartmouth(model_name="llama-3-1-8b-instruct")
# llm = ChatOpenAI(model_name="gpt-4o")


@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b


tools = [add, multiply]

llm_with_tools = llm.bind_tools(tools)


query = "What is 3 * 12? Also, what is 11 + 49?"

messages = [HumanMessage(query)]

ai_msg = llm_with_tools.invoke(messages)

print(ai_msg.tool_calls)

messages.append(ai_msg)

print(messages)

for tool_call in ai_msg.tool_calls:
    selected_tool = {"add": add, "multiply": multiply}[tool_call["name"].lower()]
    tool_msg = selected_tool.invoke(tool_call)
    messages.append(tool_msg)

print(llm_with_tools.invoke(messages))
