import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")

model_id = f"openai:{os.getenv('LLM_MODEL_ID')}"


"""
    聊天模型
"""
llm = init_chat_model(
    model=model_id,
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,
)

# 工具调用
@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."


model_with_tools = llm.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")


# 工具调用的常见方式
"""
    工具调用循环
"""

tools = [get_weather]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = llm.bind_tools(tools)

# Step 1: 模型生成工具调用
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# Step 2: 执行工具并收集结果
for tool_call in ai_msg.tool_calls:
    # 使用生成的参数执行工具
    tool = tools_by_name[tool_call["name"]]
    tool_result = tool.invoke(tool_call)
    messages.append(tool_result)

# Step 3: 将结果传回模型以获取最终响应
final_response = model_with_tools.invoke(messages)
print(final_response.text)

"""
    强制工具调用
"""
model_with_tools = llm.bind_tools([tool_name], tool_choice="any")



"""
    并行工具调用 
"""
tools = [get_weather]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = llm.bind_tools(tools)

response = model_with_tools.invoke(
    "What's the weather in Boston and Tokyo?"
)


# 模型可能生成多个工具调用
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
# ]


# 执行所有工具（可以使用异步并行完成）
# 模型会基于请求操作的独立性，智能地判断何时适合进行并行执行
results = []
for tool_call in response.tool_calls:
    tool = tools_by_name[tool_call["name"]]
    result = tool.invoke(tool_call)
    results.append(result)




"""
    流式工具调用
"""

for chunk in model_with_tools.stream(
    "What's the weather in Boston and Tokyo?"
):
    # Tool call chunks arrive progressively
    for tool_chunk in chunk.tool_call_chunks:
        if name := tool_chunk.get("name"):
            print(f"Tool: {name}")
        if id_ := tool_chunk.get("id"):
            print(f"ID: {id_}")
        if args := tool_chunk.get("args"):
            print(f"Args: {args}")
