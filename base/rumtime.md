LangGraph 暴露了一个 Runtime 对象，包含以下信息：

    上下文（Context）：静态信息，如用户 ID、数据库连接或智能体调用的其他依赖项

    存储（Store）：一个 BaseStore 实例，用于长期记忆

    流写入器（Stream writer）：用于通过 "custom" 流模式流式传输信息的对象

    执行信息（Execution info）：当前执行的身份和重试信息（线程 ID、运行 ID、尝试次数）

    服务器信息（Server info）：在 LangSmith Agent Server 上运行时特定于服务器的元数据（助手 ID、图 ID、已认证用户）


Runtime = Context + Store + Writer + Execution Info + Server Info。它不是模型上下文，而是 Agent 运行时给工具和中间件使用的依赖注入容器。

Runtime 解决的是“Agent 执行时，工具和中间件如何拿到本次运行所需的依赖和元信息”。


# context_schema 与 context：把本次运行的静态依赖注入 Agent
context_schema 和 context 解决的是“怎样把本次调用才知道的信息传给 Agent runtime”。
    用 context_schema 定义上下文结构。
    调用 agent.invoke(...) 时传入 context。
    工具或中间件通过 Runtime 读取这个 context。