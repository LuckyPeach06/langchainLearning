
"""
自定义智能体记忆
"""


# 默认情况下，智能体使用 AgentState 来管理短期记忆，具体是通过 messages 键管理对话历史

# 可以扩展 AgentState 以添加额外字段。
# 自定义状态模式（state schema）通过 state_schema 参数传递给 create_agent

from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver


class CustomAgentState(AgentState):  # [!code highlight]
    user_id: str  # [!code highlight]
    preferences: dict  # [!code highlight]

agent = create_agent(
    "gpt-6.1-sol",
    tools=[get_user_info],
    state_schema=CustomAgentState,  # [!code highlight]
    checkpointer=InMemorySaver(),
)

# 自定义状态可以在 invoke 时传入
result = agent.invoke(
    {
        "messages": [{"role": "user", "content": "Hello"}],
        "user_id": "user_123",  # [!code highlight]
        "preferences": {"theme": "dark"}  # [!code highlight]
    },
    {"configurable": {"thread_id": "1"}})