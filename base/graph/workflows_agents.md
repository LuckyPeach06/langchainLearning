# workflows
1. Prompt Chaining（提示链 / 流水线模式）
架构：A 的输出是 B 的输入，B 的输出是 C 的输入。像一条流水线。

适用场景：翻译文档、先写草稿再审核、生成 Markdown 再转 HTML。步骤固定，每一步需要专注。

Java 类比：责任链模式（Chain of Responsibility） 或 串行调用。

代码核心：add_edge("node_a", "node_b")，中间穿插个 if-else 做门禁检查。

2. Parallelization（并行化）
架构：收到任务后，分发给 3 个节点同时执行，最后合并（Aggregator）结果。

适用场景：审查代码（一个人查语法，一个人查安全，一个人查性能），或者对同一个问题用 3 个不同模型生成答案做对比。

Java 类比：CompletableFuture.allOf(...) 或者 Fork/Join 框架。

代码核心：用 START 连向 A、B、C，再用 A、B、C 连向聚合节点。注意 State 必须配 Reducer。

3. Routing（路由分发）
架构：先让大模型做一次分类（识别意图），然后通过 if-else 把任务分发给对应的专家节点（如售后节点、退款节点、技术节点）。

适用场景：客服系统。先分流，再处理，防止每个专家节点都看到所有的系统提示词。

Java 类比：Spring Cloud Gateway 或 策略模式（switch-case）。

代码核心：大模型用 with_structured_output 输出分类枚举 -> 传给 add_conditional_edges 做跳转。

4. Orchestrator-Worker（编排者-工作者 / Map-Reduce 模式）
架构：总控（Orchestrator）先看一遍任务，动态拆分出 N 个子任务，用 Send 动态并发给 N 个 Worker 去干，最后把 N 个结果拼起来。

适用场景：写长报告。总控把报告分成“引言、正文、结论”，然后并发让 Worker 分别写，最后汇总。

Java 类比：Map-Reduce 任务或动态线程池。

代码核心：Send API + Reducer 合并。


# agents
5. Evaluator-Optimizer（评估者-优化者 / 反馈循环）
架构：一个 LLM 负责写（Generator），另一个 LLM 负责打分并给修改意见（Evaluator）。写得不好就打回重写，直到通过。

适用场景：需要极高准确率的任务（如法律文书翻译、极度严谨的代码生成）。

Java 类比：带重试机制的 while 循环，或者编译器的 compile -> error -> fix -> compile。

代码核心：条件边 + 循环指回起点。

6. Agents（智能体 / 完全自主）
架构：这就是我们常说的 ReAct 模式。LLM 自己决定要不要调工具，调哪个工具，看到结果后自己决定下一步。

适用场景：开放式问题（如“帮我查一下今天北京天气，如果下雨就帮我定个车”）。

Java 类比：完全自治的微服务，没有外部网关强加路由。

代码核心：一个不断循环的图（LLM -> 工具 -> LLM），用 should_continue 决定何时结束。


# ToolNode(预置工具节点)
如果自己写工具执行的逻辑（判断工具名、传参数、捕获异常、回传 ToolMessage），代码会非常冗长。
ToolNode 直接把这些脏活全包了：
from langgraph.prebuilt import ToolNode
builder.add_node("tools", ToolNode([search, calculator]))

它支持自动注入状态（ToolRuntime）。可以让工具直接读取全局的 user_id 或外部 context，不需要让大模型把 user_id 放在参数里传进去。