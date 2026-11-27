Graph API 的控制流

# 顺序执行（Sequence）—— 直线流水线
Node 返回的字典是局部更新，没有用 Reducer 的字段会直接覆盖旧值。
from langgraph.graph import START, StateGraph

builder = StateGraph(State)

#添加节点
builder.add_node(step_1)
builder.add_node(step_2)
builder.add_node(step_3)

#添加边
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", "step_3")

# 并行分支（Branches）—— CompletableFuture 并发
从 A 分叉，B 和 C 同时执行，等它俩都完了，D 再继续执行（扇出 Fan-out 和扇入 Fan-in）

并发写同一个 State 列表，必须用 Reducer（比如 operator.add），否则 B 和 C 的结果会互相覆盖。
执行顺序是不确定的：B 和 C 谁先跑完谁先写，所以如果对顺序有要求（比如日志），得在 State 里存个时间戳或者序列号。

怎么处理长短不一的分支？（defer=True）：builder.add_node(d, defer=True)

import operator
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    # The operator.add reducer fn makes this append-only
    aggregate: Annotated[list, operator.add]


def a(state: State):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"]}


def b(state: State):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}


def c(state: State):
    print(f'Adding "C" to {state["aggregate"]}')
    return {"aggregate": ["C"]}


def d(state: State):
    print(f'Adding "D" to {state["aggregate"]}')
    return {"aggregate": ["D"]}


builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_node(d)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)
graph = builder.compile()
graph.invoke({"aggregate": []}, {"configurable": {"thread_id": "foo"}})

output：
Adding "A" to []
Adding "B" to ['A']
Adding "C" to ['A']
Adding "D" to ['A', 'B', 'C']


# 条件分支（Conditional Branching）—— Switch / 路由
A 跑完后，根据 State 里的某个值，决定走 B 还是走 C。
用 builder.add_conditional_edges("a", route_function)。这个 route_function 读入 State，返回下一个节点的名字（字符串）


import operator
from typing import Annotated, Literal, Sequence

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    aggregate: Annotated[list, operator.add]
    # Branching key set by node a
    which: str


def a(state: State):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"], "which": "c"}


def b(state: State):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}


def c(state: State):
    print(f'Adding "C" to {state["aggregate"]}')
    return {"aggregate": ["C"]}


builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_edge(START, "a")
builder.add_edge("b", END)
builder.add_edge("c", END)


def conditional_edge(state: State) -> Literal["b", "c"]:
    # Fill in arbitrary logic here that uses the state
    # to determine the next node
    return state["which"]


builder.add_conditional_edges("a", conditional_edge)

graph = builder.compile()
result = graph.invoke({"aggregate": []})
print(result)

output:
Adding "A" to []
Adding "C" to ['A']
{'aggregate': ['A', 'C'], 'which': 'c'}

# 循环（Loops）—— 带死循环保护的 While
A -> B -> A -> B，这就是 Agent 最经典的 ReAct 循环（A 是大模型思考，B 是工具执行）
必须有条件边来终止循环

import operator
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    # operator.add reducer 函数使其仅追加
    aggregate: Annotated[list, operator.add]


def a(state: State):
    print(f'Node A sees {state["aggregate"]}')
    return {"aggregate": ["A"]}


def b(state: State):
    print(f'Node B sees {state["aggregate"]}')
    return {"aggregate": ["B"]}


# 定义节点
builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)


# 定义边
def route(state: State) -> Literal["b", END]:
    if len(state["aggregate"]) < 7:
        return "b"
    else:
        return END


builder.add_edge(START, "a")
builder.add_conditional_edges("a", route)
builder.add_edge("b", "a")
graph = builder.compile()
graph.invoke({"aggregate": []})

output:
Node A sees []
Node B sees ['A']
Node A sees ['A', 'B']
Node B sees ['A', 'B', 'A']
Node A sees ['A', 'B', 'A', 'B']
Node B sees ['A', 'B', 'A', 'B', 'A']
Node A sees ['A', 'B', 'A', 'B', 'A', 'B']