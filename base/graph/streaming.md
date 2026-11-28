# 最常用的 4 种 Stream Mode
1. messages —— 打字机效果的灵魂
作用：流式输出大模型生成的每一个 Token。

数据格式：(message_chunk, metadata)。metadata 里包含 langgraph_node（这个 Token 是哪个节点生成的）和 tags（模型标签）。

实战场景：前端 LLM 对话框的“一个字一个字蹦出来”。

2. updates —— 节点状态更新（增量）
作用：某个节点执行完毕后，返回的增量状态。

输出示例：{'generate_joke': {'joke': 'Why did...'}}

实战场景：用来更新前端侧边栏的“执行进度”（比如：“资料搜索完成”）。

3. values —— 节点状态快照（全量）
作用：某个节点执行完毕后，全局 State 的全量快照。

实战场景：比如你需要在节点执行后，把整个全局的 Context（包含历史对话、检索结果等）同步给前端，做数据调试或全量 UI 渲染。

4. custom —— 自定义进度推送（大杀器）
作用：如果你想在节点里偷偷推送点“非大模型”的进度（比如：PDF 解析进度 50%），就用这个。

怎么用：
from langgraph.config import get_stream_writer
def my_node(state):
    writer = get_stream_writer()
    writer({"progress": "正在查询数据库..."})

# 3 个坑
1. 为什么包了一层 create_agent 后，前端就不打字了？
如果你用 create_agent 造了一个 Agent，然后把它作为“子图节点”塞进父图里。
此时，如果你在父图调用 stream_mode="messages"，默认是拿不到子图（Agent）内部大模型的 Token 的！
解法：必须加 subgraphs=True，让流穿透到子图内部。

2. 屏蔽敏感节点的输出（nostream 标签）
如果你的图里有一个节点专门在做“内容合规审查”或者“内部逻辑整理”，你不想把它的思考过程推给用户。
解法：初始化模型时加上 tags=["nostream"]。

internal_model = ChatAnthropic(model="...").with_config({"tags": ["nostream"]})

3. Python < 3.11 的异步上下文丢失
如果你用 async 写代码，且 Python 版本 < 3.11，get_stream_writer 可能会报错，或者拿到的是空的。
解法：手动把 config 传给 ainvoke()，或者给节点加上 writer 参数（async def my_node(state, writer: StreamWriter)）。