import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

load_dotenv()

# 1. 创建指向 DeepSeek 的模型实例
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),   
    api_key=os.getenv("LLM_API_KEY"), 
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0,
)

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# 2. 把 llm 实例传给 create_agent
agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
