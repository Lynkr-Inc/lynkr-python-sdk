from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv
import os

load_dotenv()

from lynkr import LynkrClient


lynkr_client = LynkrClient(api_key=os.getenv("LYNKR_API_KEY", ""))

lynkr_client.add_key(
    "resend",
    "x-api-key",
    os.environ.get("RESEND_API_KEY", "sample_resend_key")
)

tools = lynkr_client.langchain_tools()

model  = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    model="gpt-3.5-turbo",
)

agent = create_react_agent(
    model=model,
    tools=tools,
)

messages = [SystemMessage(content="You are a helpful assistant")]

while True: 
    user_input = input("User: ")
    if user_input.strip().lower() in {"quit", "exit", "q", "bye"}:
        print("Goodbye!")
        break
    messages.append(HumanMessage(content=user_input))
    response = agent.invoke({
    "messages": messages,
    })
    print("Response", response)
    print("AI Response: ", response["messages"][-1].content)  
    messages.append(AIMessage(content=response["messages"][-1].content))

