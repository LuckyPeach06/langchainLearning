"""
    工具执行
"""

# 在 LangChain 中，工具由智能体（Agent）使用（例如通过 create_agent），
# 工具的错误处理通过中间件（middleware）进行配置。

# 对于 LangGraph 工作流，工具的执行由 ToolNode 处理。
# 有关图 API（Graph API）的用法（包括工具如何访问当前图状态和运行作用域内的上下文），请参阅 ToolNode。



# 工具返回值：

# 返回 string，用于人类可读的结果。
# 返回 object，用于模型应解析的结构化结果。
# 返回 Command（可选附带消息），用于需要写入状态（state）的场景。

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(
        update={
            "preferred_language": language,
            "messages": [
                ToolMessage(
                    content=f"Language set to {language}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


# 直接从工具返回
# 在工具上设置 return direct 以短路（short-circuit）智能体循环：
# 智能体立即将工具的输出返回给调用方，而不会将其送回模型进行进一步处理。
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


@tool(return_direct=True)
def fetch_order_status(order_id: str) -> str:
    """Fetch the current status of a customer order."""
    # In production, query your order management system here
    return f"Order {order_id} is shipped and will arrive in 2 days."


agent = create_agent(
    ChatOpenAI(model="gpt-5.4-mini"),
    tools=[fetch_order_status],
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is the status of order #12345?"}]
})
# The agent returns the tool output directly without another LLM call:
# "Order 12345 is shipped and will arrive in 2 days."




# 错误处理
# 使用 LangChain 智能体中间件处理工具错误，以重试失败的工具调用或返回自定义错误消息：
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )

agent = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[],
    middleware=[handle_tool_errors],
)