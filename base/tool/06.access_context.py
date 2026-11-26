from langchain.tools import tool

"""访问上下文"""

# 工具可以通过 ToolRuntime 参数访问运行时信息，该参数提供：

# 组件	                                        描述	                                用例
# State（状态）	                短期记忆——当前对话期间存在的                   访问对话历史、追踪工具调用次数
#                              可变数据（消息、计数器、自定义字段）	

# Context（上下文）	            调用时传入的不可变配置（用户 ID、会话信息）	         根据用户身份个性化响应
# Store（存储）	                长期记忆——跨对话持久保存的数据	                    保存用户偏好、维护知识库
# Stream Writer（流写入器） 	        在工具执行期间发送实时更新	                展示长时间运行操作的进度

# Execution Info（执行信息）	    当前执行的身份与重试信息                 访问线程/运行 ID、根据重试状态调整行为
#                               （线程 ID、运行 ID、尝试次数）	

# Server Info（服务端信息） 	在 LangSmith Agent Server 上               访问助手 ID、图 ID 或已认证用户信息
#                                   运行时的服务端特定元数据
#                               （助手 ID、图 ID、已认证用户）	


# 短期记忆(State)
# 访问记忆
from langchain.tools import tool, ToolRuntime
from langchain.messages import HumanMessage

@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """Get the most recent message from the user."""
    messages = runtime.state["messages"]

    # Find the last human message
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content

    return "No user messages found"

# Access custom state fields
@tool
def get_user_preference(
    pref_name: str,
    runtime: ToolRuntime
) -> str:
    """Get a user preference value."""
    preferences = runtime.state.get("user_preferences", {})
    return preferences.get(pref_name, "Not set")


# 更新记忆
from langchain.agents import AgentState
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


class CustomState(AgentState):
    user_name: str


@tool
def set_user_name(new_name: str, runtime: ToolRuntime[None, CustomState]) -> Command:
    """Set the user's name in the conversation state."""
    return Command(
        update={
            "user_name": new_name,
            "messages": [
                ToolMessage(
                    content=f"User name set to {new_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )



"""上下文"""

# 上下文（Context）提供在调用时传入的不可变配置数据。
# 它适用于用户 ID、会话详情或应用特定设置等在对话期间不应发生变化的配置。
#
# 通过 runtime.context 访问上下文。配置检查点并传入带有稳定 thread_id 的 context，以便对话在多次调用之间保持持久

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.utils.uuid import uuid7

USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com",
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com",
    },
}


@dataclass
class UserContext:
    user_id: str


@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return (
            f"Account holder: {user['name']}\n"
            f"Type: {user['account_type']}\n"
            f"Balance: ${user['balance']}"
        )
    return "User not found"
