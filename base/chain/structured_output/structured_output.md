# Structured Output（结构化输出）
Structured Output 解决的是“Agent 的最终结果如何被程序稳定消费”，而不是只解决“模型如何生成 JSON”。

# Agent State（智能体 状态）
Agent state 解决的是“结构化结果最终在哪里取”，避免开发者在消息历史里到处找答案
结果最终落到 structured_response

final_state = agent.invoke({
    "messages": [
        {"role": "user", "content": "请把这段客户反馈整理成客服工单。"}
    ]
})

ticket = final_state["structured_response"]
print(ticket.category)
print(ticket.urgency)

# response_format（响应格式）：结构化输出的总开关

它解决的问题：
response_format 解决的是“开发者如何声明 Agent 的输出契约”。

官方文档里，create_agent 的 response_format 支持四种形式：

ToolStrategy[StructuredResponseT]：用工具调用实现结构化输出。
ProviderStrategy[StructuredResponseT]：使用模型供应商原生结构化输出能力。
type[StructuredResponseT]：直接传 schema 类型，让 LangChain 自动选择策略。
None：不显式要求结构化输出。

# handle_errors（错误处理策略）：决定哪些错误要自动修复

它解决的问题：
handle_errors 解决的是“结构化输出失败时，是自动重试、定制提示，还是直接抛错”。

官方文档列出了几种策略：

True：捕获所有错误，并使用默认错误模板，默认值就是这个。
str：捕获所有错误，但使用自定义错误消息。
type[Exception]：只捕获指定异常类型。
tuple[type[Exception], ...]：只捕获指定的一组异常类型。
Callable[[Exception], str]：用自定义函数生成错误消息。
False：不重试，直接让异常抛出。
