# 状态定义:TypedDict vs Pydantic
默认推荐 TypedDict：性能好，相当于在 Java 里定义的 DTO 或 Map。

进阶推荐 Pydantic：如果需要对用户的初始输入做强校验（比如要求年龄必须是数字），就用 Pydantic（相当于 Java 里的 @Valid 注解）。注意：Pydantic 只校验第一道入口，中间节点流转时不校验，且由于有反射开销，性能不如 TypedDict。

# 输入与输出分离（Input/Output Schemas）
就像写 Spring Controller，有时候你不想把 Entity 的所有字段都返回给前端，只返回 ResponseDTO。
LangGraph 允许你定义：

InputSchema：用户传进来的字段（校验）。
OutputSchema：最后 invoke 返回的字段（过滤）。
OverallState：内部节点互相通信的完整全局状态。

用法：StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)。

# 状态更新机制
节点（Node）返回的局部数据，是怎么合并进全局 State 的？

1、默认机制（覆盖 / Last-Write-Wins）
如果你什么都不做，直接 return {"foo": 1}。那么全局 State 里的 foo 就会被直接覆盖成 1。

2. 自定义合并（追加 / Append）
如果你有一个消息列表 messages，你每次都想往里加，不想覆盖。

你需要用 Annotated 注解挂载一个 Reducer（合并器）：

from typing import Annotated
from operator import add

class State(TypedDict):
    # 告诉框架：这个字段更新时，用 add 函数（即 left + right）来合并
    messages: Annotated[list, add] 


# 处理多轮对话的神器：add_messages
大模型的对话历史列表 messages，不能简单的 left + right（追加），因为如果有重复的 ID 或者要修改历史消息怎么办？
LangGraph 内置了 add_messages 合并器：

python
from langgraph.graph.message import add_messages
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

它能智能处理：如果是新消息就追加，如果是带相同 ID 的消息就替换（比如人工介入修改了之前的回复）。

# 清空合并器（Overwrite）
如果用了 add 这种合并器，你 return {"messages": []} 是清空不了的
如果非要清空（比如清空报错信息），必须用 Overwrite 包裹：
from langgraph.types import Overwrite
def clear_errors(state):
    return {"errors": Overwrite([])} # 暴力绕过合并器，强制覆盖为空