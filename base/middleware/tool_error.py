"""
捕获工具执行期间引发的异常，并将其转换为模型可以查看并从中恢复的错误 ToolMessage，
而不是中止智能体运行。工具错误适用于以下情况：

    让模型使用修正后的参数重试失败的工具调用。
    呈现受控的、经过清理的错误消息，而不是原始异常详情。
    防止意外的工具异常导致智能体崩溃。
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware

# 配置选项：
#   on_error 
#   aon_error  
#   tools  
def on_error(exc: Exception, request: ToolCallRequest) -> str | None:
    if isinstance(exc, ValueError):
        return f"`{request.tool_call['name']}` failed with {type(exc).__name__}."
    # propagate everything else


agent = create_agent(
    model="gpt-6.1-sol",
    tools=[your_tools],
    middleware=[ToolErrorMiddleware(on_error)],
)

