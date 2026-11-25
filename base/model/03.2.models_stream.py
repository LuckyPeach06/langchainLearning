import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")

model_id = f"openai:{os.getenv('LLM_MODEL_ID')}"


"""
    聊天模型
"""
llm = init_chat_model(
    model=model_id,
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,
)


# 流式输出
for chunk in llm.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="|", flush=True)
