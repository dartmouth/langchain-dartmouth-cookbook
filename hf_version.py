from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
import os
import requests

from langchain_openai import ChatOpenAI

resp = requests.post(
    "https://api.dartmouth.edu/api/jwt",
    headers={"Authorization": os.environ["DARTMOUTH_API_KEY"]},
)
jwt = resp.json()["jwt"]

headers = {"Authorization": f"Bearer {jwt}"}

URL = "https://ai-api.dartmouth.edu/tgi/llama-3-1-8b-instruct/v1/chat/completions"
llm = HuggingFaceEndpoint(endpoint_url=URL)

llm.client.headers.update(headers)

llm = ChatHuggingFace(llm=llm, model_id="meta-llama/Llama-3.1-8B-Instruct")

# response = llm.invoke(
#     """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

# Cutting Knowledge Date: December 2023
# Today Date: 23 July 2024

# You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>

# Hi, how are you?<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
# )

# print(response)

# llm = ChatOpenAI(base_url=URL + "/v1")

# llm.client._client._custom_headers.update({"Authorization": f"Bearer {jwt}"})

llm.invoke("Hi, how are you?").pretty_print()


from langchain_core.tools import tool


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

from langchain_core.messages import HumanMessage

query = "What is 3 * 12? Also, what is 11 + 49?"

messages = [HumanMessage(query)]

ai_msg = llm_with_tools.invoke(messages)

print(ai_msg.tool_calls)

messages.append(ai_msg)

for tool_call in ai_msg.tool_calls:
    selected_tool = {"add": add, "multiply": multiply}[tool_call["name"].lower()]
    tool_msg = selected_tool.invoke(tool_call)
    tool_msg.type = "ipython"
    messages.append(tool_msg)

print(messages)
print(llm_with_tools.invoke(messages))
