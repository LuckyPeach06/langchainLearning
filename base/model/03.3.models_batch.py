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


# 批处理
# 默认情况下，batch() 只会返回整个批次的最终输出。
# 如果你希望在每个单独的输入生成完成时立即接收其输出
# 你可以使用 batch_as_completed() 来流式获取结果
# 使用 batch_as_completed() 时，结果可能会乱序到达。
# 每个结果都包含输入索引，以便根据需要匹配并重建原始顺序
responses = llm.batch([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
responses = llm.batch_as_completed([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    print(response)

