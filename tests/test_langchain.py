import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to resolve relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lynkr import LynkrClient
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# --- 1. Initialize ---

# Initialize the Lynkr client
lynkr_client = LynkrClient(api_key=os.getenv("LYNKR_API_KEY", ""))

# Initialize the LLM
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    model="gpt-3.5-turbo",
)

# --- 2. Pre-load API keys ---
print("\nAdding API keys to the Lynkr client...")
lynkr_client.add_key(
    "resend",
    "x-api-key",
    os.environ.get("RESEND_API_KEY", "sample_resend_key")
)

# --- 3. Tools ---
tools = lynkr_client.langchain_tools()

# --- 4. Prompt (same as your original system message) ---
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad"],
    template="""
You are a helpful assistant that can use Lynkr APIs to perform tasks.
Ensure that you are able to have a chat with the user and whenever you are stuck you can 
talk to the user to get more information.
You have access to the following tools:
get_schema: This should be called first
- It will return the json schema of the API you are going to call
- You can use this to understand the API and its parameters
- Interact with the user to get all the required parameters and ensure that optional paramertes
are not wanted
- Then verify your understanding of users needs by asking for confirmation not in json in plaintext

Once the user confirms, you can call the execute_schema with the parameters you have gathered
---  
Now here's the user's request:

{input}

---  
And here's your scratchpad for reasoning:

{agent_scratchpad}
""")


# --- 5. Create the langgraph agent ---
agent = create_openai_tools_agent(llm, tools, prompt)
# --- 6. Wrap in an executor ---
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False
)

# --- 7. Run REPL with simple memory via chat_history ---
if __name__ == "__main__":
    chat_history: list = []
    print("Type your message (or 'quit' to exit):")
    while True:
        user_input = input("▶ ")
        if user_input.strip().lower() in {"quit", "exit", "q", "bye"}:
            print("Goodbye!")
            break

        # Invoke the agent with memory
        result = agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })

        output = result.get("output", "")
        print(f"\nAI: {output}\n")

        # Update chat history
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=output))
