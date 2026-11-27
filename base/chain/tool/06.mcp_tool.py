# MCPAdapter 会发现服务器的工具并将其转换为 LangChain 工具。
# 打开适配器，调用 list_tools()，然后将结果交给 create_agent

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter

# async with MCPAdapter("https://example.com/mcp") as adapter:
#     tools = await adapter.list_tools()
#     agent = create_agent("claude-sonnet-4-6", tools)