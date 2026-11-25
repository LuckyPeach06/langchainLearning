import os

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware,HumanInTheLoopMiddleware,PIIMiddleware,ModelRetryMiddleware,ToolRetryMiddleware
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from deepagents.backends import StateBackend
from deepagents.middleware import MemoryMiddleware, SkillsMiddleware, SummarizationMiddleware, FilesystemMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),   
    api_key=os.getenv("LLM_API_KEY"), 
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.5,
    timeout=600
)

@tool
def search(query: str) -> str:
    """Search for a query and return a short summary."""
    return f"Search results for: {query}"

backend = StateBackend()

"""
    HumanInTheLoopMiddleware: 
        某些操作上让智能体会暂停并等待；由人类进行批准、编辑或拒绝；然后执行继续。
    PIIMiddleware:
        安全拦截器。有些策略无法通过提示词来完成，通过该功能进行拦截，确保安全。

    ModelRetryMiddleware:
        容错机制，针对LLM
    ToolRetryMiddleware：
        容错机制，针对工具调用

    FilesystemMiddleware: 给 Agent 一个草稿本（存中间结果）
        文件系统中间件，赋予agent一个虚拟硬盘，允许进行write_file、read_file等文本操作
        把长文本和中间结果进行存储，主要解决LLM的token有限问题。
        相当于挂载一个缓存或者磁盘，用于缓存大对象。

    TodoListMiddleware：
        待办事项列表中间件
        赋予agent规划能力，让agent工作之前生成一个To-Do list
    SubAgentMiddleware：
        创建子智能体，赋予agent委托能力
        主agent和子agent共享一个虚拟硬盘

    SummarizationMiddleware: 给 Agent 装上“遗忘曲线”（旧对话自动摘要）
        摘要中间件
        compact功能
    MemoryMiddleware：给 Agent 植入“长期背景记忆”
        记忆中间件
        赋予 Agent “持久化的长期记忆”
    SkillsMiddleware：给 Agent 一个“技能书库”（需要什么技能现查现学）
        技能中间件
        渐进式披露
"""
agent = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[search],
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"write_file": True}),
        PIIMiddleware("email"),

        ModelRetryMiddleware(max_retries=3),
        ToolRetryMiddleware(max_retries=2),

        FilesystemMiddleware(backend=backend),

        TodoListMiddleware(),
        SubAgentMiddleware(
            backend=backend,
            subagents=[
                {
                    "name": "researcher",
                    "description": "Searches and returns a structured summary.",
                    "system_prompt": "Use the search tool to research the question and summarize key points.",
                    "tools": [search],
                    "model": "anthropic:claude-sonnet-4-6",
                    "middleware": [],
                }
            ],
        ),

        SummarizationMiddleware(model=llm, backend=backend),
        MemoryMiddleware(backend=backend, sources=["./AGENTS.md"]),
        SkillsMiddleware(backend=backend, sources=["./skills/"]),
    ],
)