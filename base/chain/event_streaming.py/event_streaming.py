
# 使用
from langchain.agents import create_agent


def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"It's always sunny in {city}!"


agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
)

stream = agent.stream_events({
    "messages": [{"role": "user", "content": "What is the weather in SF?"}],
}, version="v3")

for message in stream.messages:
    for delta in message.text:
        print(delta, end="", flush=True)

final_state = stream.output

# 智能体消息
stream = agent.stream_events(input, version="v3")

for message in stream.messages:
    print(f"[{message.node}] ", end="")
    for delta in message.text:
        print(delta, end="", flush=True)

    full_message = message.output
    usage = full_message.usage_metadata
    if usage:
        print(usage)

# 推理内容
stream = agent.stream_events(input, version="v3")

for message in stream.messages:
    for delta in message.reasoning:
        print(f"[thinking] {delta}", end="", flush=True)

    for delta in message.text:
        print(delta, end="", flush=True)




# 工具调用
# 有两个工具调用projections：
# message.tool_calls：工具调用前，流式传输参数块
# stream.tool_calls：工具调用时，流式传输工具执行的生命周期
stream = agent.stream_events(input, version="v3")

for message in stream.messages:
    for chunk in message.tool_calls:
        print(f"tool call chunk: {chunk}")

    finalized = message.tool_calls.get()
    if finalized:
        print(f"finalized tool calls: {finalized}")

for call in stream.tool_calls:
    print(f"{call.tool_name}({call.input})")
    for delta in call.output_deltas:
        print(delta, end="", flush=True)
    print(call.output, call.error)


# 流式传输子智能体
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


weather_agent = create_agent(
    model=init_chat_model("openai:gpt-6.1-sol"),
    tools=[get_weather],
    name="weather_agent",
)


def call_weather(query: str) -> str:
    """Query the weather agent."""
    result = weather_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].text


supervisor = create_agent(
    model=init_chat_model("openai:gpt-6.1-sol"),
    tools=[call_weather],
    name="supervisor",
)

stream = supervisor.stream_events(
    {"messages": [{"role": "user", "content": "What's the weather in Boston?"}]},
    version="v3",
)

for subagent in stream.subagents:
    print(f"{subagent.name}: ", end="")
    for message in subagent.messages:
        for token in message.text:
            print(token, end="", flush=True)
    print()

# 状态和最终输出
# 使用 stream.values 获取状态快照，使用 stream.output 获取最终智能体状态。
stream = agent.stream_events(input, version="v3")

for snapshot in stream.values:
    print(snapshot)

final_state = stream.output




### 多个projections：

# 要在异步代码中并发消费，请使用 astream_events 配合 asyncio.gather：
# import asyncio

# stream = await agent.astream_events(input, version="v3")

# async def consume_messages():
#     async for message in stream.messages:
#         print(await message.text)

# async def consume_tool_calls():
#     async for call in stream.tool_calls:
#         print(call.tool_name, call.input)

# await asyncio.gather(consume_messages(), consume_tool_calls())




# 对于同步代码，改用 stream.interleave(...)：
stream = agent.stream_events(input, version="v3")

for name, item in stream.interleave("messages", "tool_calls", "values"):
    if name == "messages":
        print(item.text)
    elif name == "tool_calls":
        print(item.tool_name, item.input)
    elif name == "values":
        print(item)