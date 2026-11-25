"""
构建可以回答有关文本文件问题的agent
"""

import os
import urllib.error
import urllib.request

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent
import urllib

from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """You are a literary data assistant.

## Capabilities

- `fetch_text_from_url`: loads document text from a URL into the conversation.
Do not guess line counts or positions—ground them in tool results from the saved file."""

# 1.创建工具
# 工具应具备良好的文档：其名称、描述和参数名称会成为模型提示词的一部分。
@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"获取失败:{e}"

    text = raw.decode("utf-8", errors="replace")

    return text

# 2.配置模型
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),   
    api_key=os.getenv("LLM_API_KEY"), 
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.5,
    timeout=600
)

# 3.添加记忆
# 在生产环境中，应该把消息历史保存到一个具有持久化功能的数据库中
checkpointer = InMemorySaver()



# 4.创建智能体
# 有两种不同框架用于创建智能体：LangChain和DeepAgents
# 两者区别在于，DeepAgents内置了一系列常用功能，例如规划，文件系统工具和子智能体
#
# 当你希望以最少设置获得最大能力时，使用 deep agents
# 当你需要细粒度控制时，选择 LangChain 智能体

agent = create_agent(
    model=llm,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer
)

deep_agent = create_deep_agent(
    model=llm,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


content = f"""Project Gutenberg hosts a full plain-text copy of F. Scott Fitzgerald's The Great Gatsby.
URL: https://www.gutenberg.org/files/64317/64317-0.txt

Answer as much as you can:

1) How many lines in the complete Gutenberg file contain the substring `Gatsby` (count lines, not occurrences within a line, each line ends with a line break).
2) The 1-based line number of the first line in the file that contains `Daisy`.
3) A two-sentence neutral synopsis.

Do your best on (1) and (2). If at any point you realize you cannot **verify** an exact answer with
your available tools and reasoning, do not fabricate numbers: use `null` for that field and spell out
the limitation in `how_you_computed_counts`. If you encounter any errors please report what the error was and what the error message was."""


print("Running create_agent...", flush=True)
agent_result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    },
    config={
        "configurable": 
            {
                "thread_id": "great-gatsby-lc"
            }
    }
)

print("Running create_deep_agent...", flush=True)
deep_agent_result = deep_agent.invoke(
    {
        "messages": [
            {
                "role": "user", 
                "content": content
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "great-gatsby-da"
        }
    },
)

print("\ncreate_agent:")
print(agent_result["messages"][-1].content_blocks)
print("\ncreate_deep_agent:")
print(deep_agent_result["messages"][-1].content_blocks)