# 核心原理：它是怎么存“快照”的？
1. Super-step（超步）与检查点的关系
LangGraph 不是等你整张图跑完才存一次档，而是每走完一步（Super-step），就存一次快照。

假设你的图是 START -> A -> B -> END，LangGraph 会存 4 个快照（Checkpoint）：
    开始前的空快照。
    A 执行完毕后的快照（状态：{'foo': 'a'}）。
    B 执行完毕后的快照（状态：{'foo': 'b'}）。
    结束时的快照。
这就是为什么你能做“时光倒流（Time Travel）”： 因为每一步的现场都被原封不动地存下来了。你可以随时取出第 2 步的快照，看看当时的 State 到底长啥样，甚至从那里重新跑一次。

2. 它是怎么存数据的？（底层表结构设计）
如果你用 PostgresSaver，它会建两张表（如果你自己实现 Checkpointer，也必须遵守这个规范）：
    checkpoints 表：一行代表一个超步。存的是整个 State 的序列化数据（JSON/msgpack）。
    checkpoint_writes 表：一行代表一个节点的局部输出。

为什么要两张表？ 因为 LangGraph 支持并发（比如 B 和 C 同时跑）。如果 C 挂了，B 成功了。LangGraph 会把 B 的结果先存进 writes 表。等你修复问题重新恢复时，B 不需要重跑，直接从 writes 表把 B 的结果读出来，只重跑 C 就行了。这就是文档里说的 Pending writes（挂起写入） 机制。

# 开发者最常用的 4 个关键接口
1. get_state(config)：查看当前状态
你想在页面上显示“Agent 现在想到哪一步了”，或者在调试时看看当前有没有挂起，就调这个。
state = graph.get_state(config)
print(state.values)  # 当前 State 里的数据
print(state.next)    # 下一步要执行哪个节点（如果是空元组，说明跑完了）

2. get_state_history(config)：看历史快照（排错神器）
它返回一个列表，包含这个 thread_id 下的所有历史快照（最新的排在最前面）。
你可以用代码去过滤某个特定的节点执行前的状态，或者用来自动化回放测试。

3. update_state(config)：篡改状态（人工干预）
这就是 Human-in-the-loop 弹窗审批的底层实现。人类点了个“同意”，或者直接修改了审批理由，LangGraph 会调这个方法，生成一个新的 Checkpoint，然后继续往下跑。

4. graph.invoke(None, config)：断点续传
如果你传 graph.invoke(新输入, config)，它会从 START 节点重新跑一轮。

如果你传 graph.invoke(None, config)，它会加载最新的快照，只跑剩下的（未完成的）节点。这就是用来恢复报错或中断的。

# 生产环境4 个天坑
1. 无限膨胀的 Checkpoint（存储成本危机）
如果用户跟你聊了 1000 句话，你的 checkpoints 表里就会积累上千条快照。数据库迟早撑爆。

解法：用定时任务定期清理（比如只保留最近 30 天的），或者使用文档推荐的 DeltaChannel（只存增量变更，不存全量快照，但它是 Beta 版）。

2. PostgreSQL 的 thread_id 长度超限
默认的数据库字段可能是 VARCHAR(255)。如果你的 thread_id 很长（比如拼接了超长的业务参数），数据库会直接抛异常。

解法：用 UUID 或哈希，确保 thread_id 长度不超过 255。

3. 子图跨图更新的数据丢失
由于父子图有各自独立的 Checkpoint 命名空间（checkpoint_ns），如果要跨图共享数据，父图必须配置 Reducer，或者使用上一章学的 Store。

4. 同步与异步的错配
如果你写的是 async def 的节点，但调用的却是同步的 .invoke()，或者用了一个同步的 SqliteSaver，整个流程可能会被阻塞或者报错。

线上用 AsyncPostgresSaver，本地测试用 AsyncSqliteSaver，并配合 graph.ainvoke() 使用。

# Durability（持久化级别）
在调用 graph.stream() 或 invoke() 时可以指定它：

"exit"：只有整个图跑完（或挂起）才存盘。性能最好，但中途断电就全丢了。
"sync"：每走一步都同步存盘。极度安全，但性能开销极大。
"async"：异步存盘（默认）。在性能和安全性之间取得平衡，但进程崩溃有极小概率丢失最后一两步的数据。

生产建议：金融类高危业务用 "sync"，普通聊天助手用 "async"。