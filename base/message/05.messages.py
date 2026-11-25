import os

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import add_notification_metadata, get_notification_metadata

os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")
llm = init_chat_model(f"openai:{os.getenv('LLM_MODEL_ID')}")

system_msg = SystemMessage("You are a helpful assistant.")
human_msg = HumanMessage("Hello, how are you?")

# Use with chat models
messages = [system_msg, human_msg]
response = llm.invoke(messages)  # Returns AIMessage

# 消息类型 (Message types):
#       系统消息 (System message) - 告诉模型如何表现，并为交互提供上下文
#       人类消息 (Human message) - 代表用户输入以及与模型的交互
#       AI 消息 (AI message) - 模型生成的响应，包括文本内容、工具调用和元数据
#       工具消息 (Tool message) - 代表工具调用的输出


# 消息格式
# 1、文本格式
response = llm.invoke("Write a haiku about spring")
# 2、消息提示词
messages = [
    SystemMessage("You are a poetry expert"),
    HumanMessage("Write a haiku about spring"),
    AIMessage("Cherry blossoms bloom...")
]
response = llm.invoke(messages)
# 3、字典格式
messages = [
    {"role": "system", "content": "You are a poetry expert"},
    {"role": "user", "content": "Write a haiku about spring"},
    {"role": "assistant", "content": "Cherry blossoms bloom..."}
]
response = llm.invoke(messages)

# Notifications 通知
# 消息元数据标记
# 在复杂的 Agent 系统里，很多时候后台中间件（Middleware）会自动往对话里加消息
# 如果这些消息不加以区分，直接传给你的 Web 前端，前端只会当成普通对话展示，
# 用户会一脸懵逼：“我没发过这句话啊，哪来的‘任务完成’？”
notification = add_notification_metadata(
    HumanMessage("Background task t_42 finished."), # 原本是个普通的用户消息
    source="background_job",                        # 标记来源：后台任务
    data={"task_id": "t_42", "status": "success"}   # 附加业务数据
)

for message in messages:
    metadata = get_notification_metadata(message)
    if metadata is None:
        # 普通消息（用户真正说的话 或 大模型真正说的话）
        print(message.text)  # A regular message
    else:
        # 带有通知标签的消息（系统自动生成的）
        print(f"[{metadata['source']}]", metadata.get("data"))