# 六类 hook 把控制权放到 Agent 生命周期中

六类 hook 分别对应不同的生命周期语义：

    before_agent：一次 invoke 刚开始，适合初始化运行级字段或做入口检查；
    before_model：每轮模型调用前都会经过，适合校验消息、更新 State 或决定跳转；
    wrap_model_call：真正包住模型调用，可修改请求、短路、缓存、重试或 fallback；
    after_model：模型响应已经进入执行链，适合统计、校验或根据结果更新 State；
    wrap_tool_call：包住每个工具调用，可做权限、审批、重试和错误转换；
    after_agent：本次 Agent 执行结束，适合收口审计和运行级汇总。

# node-style 管固定节点，wrap-style 管一次调用