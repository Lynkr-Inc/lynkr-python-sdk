import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to resolve relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from src.lynkr import LynkrClient

load_dotenv()

# --- 1. Initialize ---

# Initialize the Lynkr client
lynkr_client = LynkrClient(api_key="")
llm = ChatOpenAI(temperature=0, openai_api_key="")

# --- 2. Pre-load API keys ---
print("\nAdding API keys to the Lynkr client...")

# Add service keys from environment variables
lynkr_client.keys.add("resend", os.environ.get("RESEND_API_KEY", "sample_resend_key"))

# Add a custom key with explicit field mappings
# lynkr_client.keys.add(
#     "wealthsimple", 
#     os.environ.get("WEALTHSIMPLE_API_KEY", "sample_wealthsimple_key"),
#     ["access_token", "auth_token", "ws_api_key"]
# )

# List available keys (values are masked for security)
print("\nAvailable API keys:", lynkr_client.keys.list())

# --- 3. Tools ---
tools  = lynkr_client.langchain_tools()

# Initialize the LangChain agent with the custom tool and LLM
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Invoke the agent with a natural language task
while True:
    # Initialize message chain if not already done
    message_chain = [{
    "role": "system", 
     "content": """
        You are a helpful assistant who uses Lynkr tools to help users complete tasks like sending emails, booking appointments, making reservations, checking account information, or processing data.

        When someone asks for help with a task:

        1. Use the get_schema tool first with a simple, clear phrase that captures the essence of what they want (like 'booking flight' or 'sending email')

        2. Review the schema information carefully to understand:
        - What required fields need to be filled in
        - What optional fields might enhance the experience 
        - Which sensitive fields (like API keys) we already have stored
        - Which sensitive fields we might need to ask for

        3. If we already have API keys stored for this service, let the user know by saying something like 'Good news! I already have access to the [service] API'

        4. Gather any missing information by asking questions in a natural, conversational way:
        - Ask for required fields first, one or two at a time
        - Suggest reasonable options when appropriate
        - Avoid technical jargon - keep it simple and friendly

        5. Once you have all the required information:
        - Double-check the most important details with the user
        - Use the execute_action tool to complete the task
        - The system will automatically use any stored API keys, you do not need to provide them in the filled schema

        6. Confirm task completion in simple, everyday language:
        - Share the key information from the result
        - Focus on what matters to the user, not technical details
        - Offer to help with anything else they might need

        Always maintain a friendly, helpful tone throughout the conversation. Focus on helping the user accomplish their goal without getting caught up in technical explanations unless they specifically ask for them.
        """
    }]

    user_input = input("Enter your message (type 'quit' to exit): ")
    
    # Check if user wants to quit
    if user_input.lower() in ['quit', 'exit', 'q', 'bye']:
        print("Ending conversation. Goodbye!")
        break
    
    # Add user message with proper LangChain format
    message_chain.append({"role": "human", "content": user_input})
    
    # Get AI response
    ai_response = agent.invoke(message_chain)
    print(f"AI: {ai_response["output"]}")

    # Add AI response to message chain with proper LangChain format
    message_chain.append({"role": "ai", "content": ai_response})