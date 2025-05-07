from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def create_completion(messages, tools=None, tool_choice=None):
    params = {
        "model": "gpt-4o",
        "messages": messages
    }
    if tools is not None:
        params["tools"] = tools
    if tool_choice is not None and tools is not None:
        params["tool_choice"] = tool_choice

    return client.chat.completions.create(**params)
