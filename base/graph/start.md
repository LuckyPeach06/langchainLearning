##### 总结：
LangGraph 的 Graph API 本质上就是一个状态机（State Machine）


核心心智模型：Graph API = 状态机
在写代码前，脑子里要有一张图：
    State（状态）：全局共享数据（相当于 Java 里的 ThreadLocal 或工作流的全局 Context）。
    Node（节点）：执行具体业务逻辑的函数（相当于 Java 里的 Service 方法）。
    Edge（边）：节点之间的跳转规则（相当于 if-else 路由或状态机流转）。
    Command（指令）：节点执行完后，既返回数据更新 State，又决定下一个去哪个节点。

构建客服 Agent 的 5 个步骤：
    Step 1: 画流程图（拆解节点）
        不要一上来就写 Prompt。先像画微服务架构图一样，把流程拆成独立的 Node。
        固定流向（Solid arrows）：读取邮件 -> 分类意图。就像代码里写死的串行调用。
        动态路由（Dashed arrows）：分类意图 完之后，根据分类结果，决定是去 查文档、建Bug单 还是直接 起草回复。这就需要在节点里返回 Command 来控制流向。

    Step 2: 定义每个节点的类型（定接口）
        这一步是决定代码怎么写。节点分四种：
            LLM 节点（如“分类意图”、“起草回复”）：调用大模型，需要静态 Prompt 和动态 State。
            数据节点（如“查文档”）：调外部 API，必须配重试策略（Retry），防止网络抖动。
            动作节点（如“发送邮件”、“建 Bug 单”）：产生副作用，绝对不能重试（防重复发邮件），且只在审批通过后执行。
            人工节点（如“人工审核”）：用 interrupt() 暂停，等待人类操作。

    Step 3: 设计全局 State（定义数据结构）
        这就相当于 Java 里定义 Class。原则是：只存原始数据，不存格式化的 Prompt 字符串。 因为不同节点可能要用同一份数据拼不同的 Prompt。
    
    Step 4: 实现节点（写业务代码）
        每个 Node 都是一个 Python 函数。它们接收 State，干活，然后返回要修改的数据。
        这里有一个非常关键的设计：如果你要在这个节点改变流程走向，不要用普通的 return {"next": "xxx"}，而是要返回 Command（指令）。

        如何处理错误？
            网络超时：配置自动重试（Retry）。
            LLM 解析失败：把错误存进 State，路由回 LLM 让它重新生成。
            缺信息/需审批：用 interrupt() 挂起，等人来填。

    Step 5: 编译图并运行（装配）
        把所有 Node 和 Edge 串起来。这时候，你的工作流引擎就搭建好了，可以跑 graph.compile() 了。


# 从你想要自动化的流程开始
想象你需要构建一个处理客户支持电子邮件的 AI 智能体。你的产品团队给了你这些需求：

智能体应该：

- 读取传入的客户电子邮件
- 按紧急程度和主题对它们进行分类
- 搜索相关文档以回答问题
- 起草适当的回复
- 将复杂问题升级给人工智能体

要处理的示例场景：

1. 简单的产品问题："How do I reset my password?"
2. Bug 报告："The export feature crashes when I select PDF format"
3. 紧急账单问题："I was charged twice for my subscription!"
4. 功能请求："Can you add dark mode to the mobile app?"
5. 复杂技术问题："Our API integration fails intermittently with 504 errors"


# 1、将你的工作流映射为离散步骤
首先识别流程中不同的步骤。每个步骤成为一个节点（执行一项特定功能的函数）。
然后勾勒这些步骤如何连接。在编写代码之前完成此操作。

Read Email：提取并解析电子邮件内容

Classify Intent：使用 LLM 对紧急程度和主题进行分类，然后路由到搜索、Bug 跟踪或起草

Doc Search：查询你的知识库以获取相关信息

Bug Track：在跟踪系统中创建或更新问题

Draft Reply：生成适当的响应，然后路由到人工审查或发送

Human Review：升级给人工智能体以进行批准或处理

Send Reply：发送电子邮件响应

# 2、确定每个步骤需要做什么
LLM 步骤：
    当步骤需要理解、分析、生成文本或做出推理决策时：
        分类意图：
            静态上下文（提示词）：分类类别、紧急程度定义、响应格式
            动态上下文（来自状态）：电子邮件内容、发件人信息
            期望结果：决定路由的结构化分类
        起草回复：
            静态上下文（提示词）：语气指南、公司政策、响应模板
            动态上下文（来自状态）：分类结果、搜索结果
            期望结果：可供审查的专业电子邮件响应

数据步骤：
    当步骤需要从外部源检索信息时：
        文档搜索：
            参数：根据意图和主题构建的查询
            重试策略：是，针对瞬态故障使用指数退避
            缓存：可以缓存常见查询以减少 API 调用

操作步骤：
    当步骤需要执行外部操作时：
        发送回复：
            何时执行：批准后（人工或自动）
            重试策略：是，针对网络问题使用指数退避
            不应缓存：每次发送都是唯一操作
        Bug 跟踪：
            何时执行：当意图为 "bug" 时始终执行
            重试策略：是，对于不丢失 Bug 报告至关重要
            返回：要包含在响应中的工单 ID

用户输入步骤：
    当步骤需要人工干预时：
        人工审查：
            决策上下文：原始电子邮件、草稿响应、紧急程度、分类
            预期输入格式：批准布尔值加上可选的已编辑响应
            触发时机：高紧急程度、账单或复杂问题
            拒绝时：结束运行而不发送（人工在图外部处理电子邮件）

# 3、设计你的状态
对每条数据问自己这些问题：
    它是否需要在步骤之间持久存在？如果是，它进入状态。
    你能从其他数据推导出它吗？如果是，在需要时计算它，而不是将其存储在状态中。

对于电子邮件智能体，跟踪：
    原始电子邮件和发件人信息（以后无法重建这些）
    分类结果（后续节点需要）
    搜索结果或工单上下文（重新获取成本高昂）
    草稿响应（需要通过审查持久存在）
    执行元数据（用于调试和恢复）

保持状态原始，按需格式化提示词：
    在状态中存储原始数据，而不是格式化的提示词文本。在需要时在节点内格式化提示词。

        这种分离意味着：
            不同的节点可以以不同方式格式化相同的数据
            你可以更改提示词模板而无需更改状态模式
            调试显示每个节点接收到的数据，而不是预先嵌入的提示词字符串

from typing import Literal, TypedDict


class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str


class EmailAgentState(TypedDict):
    email_content: str
    sender_email: str
    email_id: str
    classification: EmailClassification | None
    search_results: list[str] | None  # 文档或工单上下文
    draft_response: str | None

# 4、构建你的节点
节点是一个 Python 函数，它接收当前状态并返回对它的更新。当节点还选择下一步时，返回一个 Command。

适当处理错误：
    在填写节点主体之前，考虑每个节点可能如何失败。在调用外部 API 的节点上附加重试。使用 interrupt() 获取人工输入。

    对于此示例，在添加可能遇到瞬态故障的节点时附加重试策略：
    from langgraph.types import RetryPolicy

    workflow.add_node(
        "search_documentation",
        search_documentation,
        retry_policy=RetryPolicy(max_attempts=3),
    )

实现电子邮件智能体节点：
    将每个工作单元转化为一个节点。每个节点读取共享状态，完成一项工作，并返回更新。当下一步取决于结果时，返回一个包含更新和目标地的 Command。人工审查仍然是一个节点：它在函数内部调用 interrupt()，而不是单独的图原语。

# 5、将它们连接起来
将节点连接成一个图。因为路由位于 Command 节点内部，你只需要几个固定边。使用检查点存储进行编译，这是 interrupt() 暂停和恢复所必需的。