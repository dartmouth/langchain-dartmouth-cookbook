import requests
import os

resp = requests.post(
    "https://api.dartmouth.edu/api/jwt",
    headers={"Authorization": os.environ["DARTMOUTH_API_KEY"]},
)
jwt = resp.json()["jwt"]

URL = "https://ai-api.dartmouth.edu/tgi/llama-3-1-8b-instruct/v1/chat/completions"
GENERATE_ENDPOINT = "https://ai-api.dartmouth.edu/tgi/llama-3-1-8b-instruct/generate"

headers = {
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json",
}

data = """{
    "model": "tgi",
    "messages": [
        {
            "role": "user",
            "content": "What is the weather like in New York?"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "0",
                    "type": "function",
                    "function": {
                        "arguments": "{'format': 'celsius', 'location': 'New York}",
                        "name": "get_current_weather"
                    }
                }
            ]
        },
        {
            "role": "ipython",
            "content": "{'temperature': '18', 'unit': 'celsius'}",
            "tool_call_id": "0"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "format": {
                            "type": "string",
                            "enum": [
                                "celsius",
                                "fahrenheit"
                            ],
                            "description": "The temperature unit to use. Infer this from the users location."
                        }
                    },
                    "required": [
                        "location",
                        "format"
                    ]
                }
            }
        }
    ],
    "tool_choice": "get_current_weather"
}
"""

response = requests.post(URL, data=data, headers=headers)
print(response.json())


prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>


Environment: ipython
Tools: brave_search, wolfram_alpha
Cutting Knowledge Date: December 2023
Today Date: 23 July 2024

# Tool Instructions
- Always execute python code in messages that you share.
- When looking for real time information use relevant functions if available else fallback to brave_search



You have access to the following functions:

Use the function 'get_current_weather' to: Get the current weather
{"name": "get_current_weather", "description": "Get the current weather", "parameters": {"location": {"param_type": "str", "description": "The city and state, e.g. San Francisco, CA", "required": true}, "format": {"param_type": "str", "description": "The temperature unit to use. Infer this from the users location.", "required": true}}}


If a you choose to call a function ONLY reply in the following format:
<{start_tag}={function_name}>{parameters}{end_tag}
where

start_tag => `<function`
parameters => a JSON dict with the function argument name as key and function argument value as value.
end_tag => `</function>`

Here is an example,
<function=example_function_name>{"example_name": "example_value"}</function>

Reminder:
- Function calls MUST follow the specified format
- Required parameters MUST be specified
- Only call one function at a time
- Put the entire function call reply on one line
- Always add your sources when using search results to answer the user query

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What is the weather like in New York?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

<function=get_current_weather>{"location": "New York", "format": "celsius"}</function><|eom_id|><|start_header_id|>ipython<|end_header_id|>

{'temperature': '18', 'unit': 'celsius'}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

response = requests.post(GENERATE_ENDPOINT, headers=headers, json={"inputs": prompt})
print(response.json())
