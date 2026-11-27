"""
    用法
"""

# 要为智能体添加短期记忆（线程级持久化），
# 需要在创建智能体时指定一个 checkpointer（检查点保存器）。
# 使用 checkpointer 将状态持久化到数据库（或内存）中，以便线程可以在任何时候恢复。

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  # [!code highlight]


def get_user_info() -> str:
    """Look up information about the current user."""
    return "No user profile on file."


agent = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[get_user_info],
    checkpointer=InMemorySaver(),  # [!code highlight]
)

thread_config = {"configurable": {"thread_id": "1"}}
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Hi! My name is Bob."}]},
    thread_config,  # [!code highlight]
)["messages"][-1].content

print(response)  # "Hi Bob! Nice to see you here. How are you doing?"





