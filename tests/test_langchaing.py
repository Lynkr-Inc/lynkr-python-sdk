import os
from dotenv import load_dotenv

from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from lynkr.client import LynkrClient

load_dotenv()

# --- 1. Initialize ---

# Initialize the Lynkr client
lynkr_client = LynkrClient(api_key=os.environ["LYNKR_API_KEY"])
llm = ChatOpenAI(temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"])
# --- 2. Authentication --- 
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
    "content": "You are a helpful assistant who uses Lynkr tools to \
        help users complete tasks. When someone asks for help with \
        things like emails, appointments, bookings, or data processing: \
        1. Use the get_schema tool first with a simple phrase \
        (like 'booking flight' or 'sending email') \
        2. Look at what information is needed \
        3. Ask for missing details in a friendly way \
        4. Use execute_schema to complete the task once you have all \
        details \
        5. Confirm when it's done in simple language \
        Keep things conversational and natural - focus on helping \
        the user, not explaining technical details."
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