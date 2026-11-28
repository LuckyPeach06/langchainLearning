# Send —— 动态并发（Map-Reduce）

痛点场景：
假设大模型说：“请帮我查一下 lions、elephants、penguins 这三种动物的笑话。”
你事先根本不知道大模型会吐出多少个词（可能是 3 个，也可能是 30 个）。如果你用普通的 add_edge 连到“查笑话”节点，它只能处理一个。

Send 的解决方式：
它在运行时动态“扇出（Fan-out）”。你返回一个 Send 的列表，LangGraph 就会为你列表里的每一项开启一个并发的子任务。

import operator
from typing_extensions import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class OverallState(TypedDict):
    topic: str
    subjects: list[str]
    jokes: Annotated[list[str], operator.add]
    best_selected_joke: str


class JokeState(TypedDict):
    subject: str


def generate_topics(state: OverallState):
    return {"subjects": ["lions", "elephants", "penguins"]}


def generate_joke(state: JokeState):
    joke_map = {
        "lions": "Why don't lions like fast food? Because they can't catch it!",
        "elephants": "Why don't elephants use computers? They're afraid of the mouse!",
        "penguins": "Why don't penguins like talking to strangers at parties? Because they find it hard to break the ice.",
    }
    return {"jokes": [joke_map[state["subject"]]]}


def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]


def best_joke(state: OverallState):
    return {"best_selected_joke": "penguins"}


builder = StateGraph(OverallState)
builder.add_node("generate_topics", generate_topics)
builder.add_node("generate_joke", generate_joke)
builder.add_node("best_joke", best_joke)
builder.add_edge(START, "generate_topics")
builder.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
builder.add_edge("generate_joke", "best_joke")
builder.add_edge("best_joke", END)
graph = builder.compile()

1、START 启动。
2、进入 generate_topics 节点，生成 ["lions", "elephants", "penguins"]。
3、触发条件边 continue_to_jokes。它返回 3 个 Send 对象，瞬间分裂成 3 个并发分支。
4、3 个并发的 generate_joke 节点同时执行，每个节点分别拿到一个动物。
5、3 个节点执行完毕后，状态合并（Reducer 工作），把所有笑话拼成一个列表。
6、进入 best_joke 节点，评选出最佳笑话。
7、结束。

# Command —— 状态更新与路由合一
Command 允许在 Node 的 return 语句里，一句话同时更新状态并决定函数的去向

# 跨图路由（Command.PARENT）
如果在写子图（Subgraph），子图里的节点想指挥父图里的节点，
就可以在 Command 里加上 graph=Command.PARENT：

import operator
import random
from typing_extensions import Annotated, TypedDict

from langgraph.graph import START, StateGraph
from langgraph.types import Command


class State(TypedDict):
    foo: Annotated[str, operator.add]


def node_a(state: State) -> Command:
    print("Called A")
    value = random.choice(["a", "b"])
    goto = "node_b" if value == "a" else "node_c"

    return Command(
        update={"foo": value},
        goto=goto,
        # Closest parent graph relative to this subgraph
        graph=Command.PARENT,
    )


subgraph = StateGraph(State).add_node(node_a).add_edge(START, "node_a").compile()


def node_b(state: State):
    print("Called B")
    # Reducer appends; do not manually concatenate onto state["foo"]
    return {"foo": "b"}


def node_c(state: State):
    print("Called C")
    return {"foo": "c"}


builder = StateGraph(State)
builder.add_edge(START, "subgraph")
builder.add_node("subgraph", subgraph)
builder.add_node(node_b)
builder.add_node(node_c)

graph = builder.compile()



在这段代码中，子图执行以下逻辑时：
    def node_a(state: State) -> Command:
        print("Called A")
        value = random.choice(["a", "b"])
        goto = "node_b" if value == "a" else "node_c"

        return Command(
            update={"foo": value},
            goto=goto,
            # Closest parent graph relative to this subgraph
            graph=Command.PARENT,
        )

    return 的 Command，最终是交给“父图”来执行的。
    把这个过程拆成两半来看：一半是“提交给谁”，另一半是“谁来执行”。
        1. 提交给谁？（它交给了子图引擎）
            这个 return 语句写在 node_a 里，所以它是返回给当前正在运行它的“子图引擎”的。
            子图引擎（那个只会看着子图内部地图的调度员）拿到了这个 Command，第一眼看到的是：

            update={"foo": "a"}（去更新状态）
            goto="node_b"（去哪）

        2. 谁来执行？（父图接管了执行）
            正常情况下，子图引擎看到 goto="node_b"，会去它自己的地图里找 node_b。如果没加 graph=Command.PARENT，它找不到就会直接崩溃报错。

            但是！因为你在 Command 里塞了 graph=Command.PARENT，这就相当于给这个指令贴了一张“转交上级”的标签。

            子图引擎看到这个标签后，它的动作是：
            停止自己往下走。
            把 update 里的数据打包好，连同 goto 指令一起，向上级（父图）发起“越狱”交接。
            父图引擎接收到之后，在父图的地图里找 node_b 或者 node_c，并执行它们。



    #### 既然最后都要回父图，为什么要脱裤子放屁，先套一个子图？
    1、假设你在做一个“企业级客服系统”。

        父图（总控中心）：负责接收用户请求，分发给不同的处理部门。
        子图 A（退款审批流）：这是一个极其复杂的流程，包含查订单、校验金额、财务审批、打款 4 个节点。
        子图 B（技术支援流）：包含查 bug、建工单、回复 3 个节点。
        子图 A 和 子图 B 是可以独立编译、独立测试的。它们不仅在这一个系统里用，还可以打包给其他项目用（相当于一个微服务）。

        如果没有 Command.PARENT：
        子图 A 的最后一个节点做完后，必须把结果一层层 return 回父图。父图要写一大堆 if-else，判断：“哦，退款子图回来了，下一个该去技术支援了”。这导致路由逻辑高度耦合。

        有了 Command.PARENT：
        子图 A 内部可以极其“越权”地直接喊话：“我这块业务处理完了，总控中心，请把任务转交给【技术支援子图】”。
        这就是解耦。父图不需要知道子图内部经历了什么，子图直接夺过方向盘开向下一站。

    2、Human-in-the-loop（人工介入时的中断恢复）
        这是最致命的场景。
        假设子图是一个包含人工审批（interrupt）的子流程，它可能挂在后台等待一天。如果它作为父图的普通节点，中断恢复的复杂度极高。

        但有了 Command.PARENT：
        子图在某个节点挂起。
        用户在一天后点击了“同意”。

        子图恢复执行，执行完毕后，直接抛出 Command.PARENT 告诉系统：“我已经处理完，不用回到父图的等待逻辑，直接跳转到 node_b 去做收尾工作”。

            