from langchain.agents import create_agent
from langchain.mcp import MCPAdapter


async def main():
    async with MCPAdapter("https://example.com/mcp") as adapter:
        tools = await adapter.list_tools()
        agent = create_agent("claude-sonnet-5", tools)
        return await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})





from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain.messages import ToolMessage


async def access_multimodal_tool_content(server) -> dict:
    async with MCPAdapter(server) as adapter:
        tools = await adapter.list_tools()
        agent = create_agent("claude-sonnet-5", tools)
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Take a screenshot."}]}
        )

    # MCP 结果以 LangChain 内容块的形式到达。图像和文件内容
    # 与 `text` 一起转换为标准化的 `image`/`file` 块。
    for message in result["messages"]:
        if not isinstance(message, ToolMessage):
            continue
        for block in message.content_blocks:  # [!code highlight]
            if block["type"] == "text":  # [!code highlight]
                print(f"Text: {block['text']}")  # [!code highlight]
            elif block["type"] == "image":  # [!code highlight]
                preview = block.get("base64", "")[:20]  # [!code highlight]
                print(f"Image mime type: {block.get('mime_type')}")  # [!code highlight]
                print(f"Image base64: {preview}...")  # [!code highlight]

    return result