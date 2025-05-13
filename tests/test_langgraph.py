from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv
import os
import asyncio 
load_dotenv()

from lynkr import LynkrClient

print("Lynkr API CLIENT", os.getenv("LYNKR_API_KEY", ""))
lynkr_client = LynkrClient(api_key=os.getenv("LYNKR_API_KEY", ""), base_url="http://localhost:8000")

lynkr_client.add_key(
    "resend",
    "x-api-key",
    os.environ.get("RESEND_API_KEY", "")
)

tools = lynkr_client.langchain_tools()
# print("Tools: ", tools) 
# print("Tools Type: ", type(tools[0]))
# get_schema_tool = tools[0]
# response = asyncio.run(get_schema_tool("I want to send an emai"))
# print("Response: ", response)

model  = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    model="o4-mini",
    temperature=1,
)

agent = create_react_agent(
    model=model,
    tools=tools,
)

prompt = """
You are LynkrGPT, an agent that fulfills user requests by orchestrating two tools:

  1. get_schema(request_string: str)
  2. execute_schema(schema_data: dict, ref_id: str, service: str)

Always:
 - Decide whether you still need a schema.  
 - If so, call get_schema.  
 - Check the message in the response to see if you need to ask for sensitive information  
 - See the schema example and ensure you have at least all of those fields, call execute_schema. 
 - Execute schema will take the, ref_id, and service from get_schema and at the minimum the filled schema_example as schema_data. 
 - Upon success, reply with a clear, final confirmation and stop.
 - If you ever lack information, ask a clarifying question instead of guessing.

Begin!
"""

messages = [SystemMessage(content=prompt)]

while True: 
    user_input = input("User: ")
    if user_input.strip().lower() in {"quit", "exit", "q", "bye"}:
        print("Goodbye!")
        break
    messages.append(HumanMessage(content=user_input))
    response = agent.invoke({
    "messages": messages,
    })

    print("AI Response: ", response["messages"][-1].content)  
    messages.append(AIMessage(content=response["messages"][-1].content))

