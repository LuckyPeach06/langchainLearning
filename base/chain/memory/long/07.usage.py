"""
长期记忆让你的智能体能够跨不同的对话和会话存储和召回信息。
与范围仅限于单个线程的短期记忆不同，长期记忆跨线程持久存在，并且可以随时被召回。

长期记忆构建于 LangGraph 存储之上，
将数据保存为按命名空间（namespace）和键（key）组织的 JSON 文档。
"""

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from langgraph.store.memory import InMemoryStore

# InMemoryStore 将数据保存到内存字典中。在生产环境中请使用数据库支持的存储。
store = InMemoryStore()

agent: Runnable = create_agent(
    "claude-sonnet-4-6",
    tools=[],
    store=store,
)






from collections.abc import Sequence

from langgraph.store.base import IndexConfig
from langgraph.store.memory import InMemoryStore


def embed(texts: Sequence[str]) -> list[list[float]]:
    # 替换为实际的嵌入函数或 LangChain 嵌入对象
    return [[1.0, 2.0] for _ in texts]


# InMemoryStore 将数据保存到内存字典中。在生产环境中请使用数据库支持的存储。
store = InMemoryStore(index=IndexConfig(embed=embed, dims=2))
user_id = "my-user"
application_context = "chitchat"
namespace = (user_id, application_context)
store.put(
    namespace,
    "a-memory",
    {
        "rules": [
            "User likes short, direct language",
            "User only speaks English & python",
        ],
        "my-key": "my-value",
    },
)
# 通过 ID 获取“记忆”
item = store.get(namespace, "a-memory")
# 在此命名空间内搜索“记忆”，按内容等价性过滤，按向量相似度排序
items = store.search(
    namespace, filter={"my-key": "my-value"}, query="language preferences"
)




# 读取长期记忆

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.runnables import Runnable
from langgraph.store.memory import InMemoryStore


@dataclass
class Context:
    user_id: str


# InMemoryStore 将数据保存到内存字典中。在生产环境中请使用数据库支持的存储。
store = InMemoryStore()

# 使用 put 方法将示例数据写入存储
store.put(
    (
        "users",
    ),  # 将相关数据分组在一起的命名空间（用于用户数据的 users 命名空间）
    "user_123",  # 命名空间内的键（用户 ID 作为键）
    {
        "name": "John Smith",
        "language": "English",
    },  # 为给定用户存储的数据
)


@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """查找用户信息。"""
    # 访问存储 - 与提供给 `create_agent` 的存储相同
    assert runtime.store is not None
    user_id = runtime.context.user_id
    # 从存储中检索数据 - 返回包含值和元数据的 StoreValue 对象
    user_info = runtime.store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"


agent: Runnable = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[get_user_info],
    # 将存储传递给智能体 - 使智能体能够在运行工具时访问存储
    store=store,
    context_schema=Context,
)

# 运行智能体
agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    context=Context(user_id="user_123"),
)