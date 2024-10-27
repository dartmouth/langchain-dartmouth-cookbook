from openai import OpenAI
import json

import os
import requests

resp = requests.post(
    "https://api.dartmouth.edu/api/jwt",
    headers={"Authorization": os.environ["DARTMOUTH_API_KEY"]},
)
jwt = resp.json()["jwt"]


BASE_URL = "https://ai-api.dartmouth.edu/tgi/llama-3-1-8b-instruct/v1/"
client = OpenAI(base_url=BASE_URL, api_key="not-used")
client._custom_headers.update({"Authorization": f"Bearer {jwt}"})

MODEL_NAME = "Meta-Llama-3.1-8B-Instruct"

completion = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)

print(completion.choices[0].message)

# Define available function
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the user's location.",
                },
            },
            "required": ["location", "format"],
        },
    },
}

messages = [
    {
        "role": "system",
        "content": f"[AVAILABLE_TOOLS] {json.dumps(weather_tool)} [/AVAILABLE_TOOLS]"
        "You're a helpful assistant! Use tools if necessary, and reply in a JSON format",
    },
    {
        "role": "user",
        "content": "Is it hot in Pittsburgh, PA right now? long answer please",
    },
]

chat_response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages,
    tools=[weather_tool],
    tool_choice="auto",
    stream=False,
)

assistant_message = chat_response.choices[0].message
messages.append(assistant_message)

tool_call_result = 88
tool_call_id = assistant_message.tool_calls[0].id
tool_function_name = assistant_message.tool_calls[0].function.name
messages.append(
    {
        "role": "tool",
        "content": str(tool_call_result),
        "tool_call_id": tool_call_id,
        "name": tool_function_name,
    }
)

print(messages)

chat_response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages,
    tools=[weather_tool],
    tool_choice="auto",
    stream=False,
)

assistant_message = chat_response.choices[0].message

print(chat_response)
