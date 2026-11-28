LangGraph 提供了两套完全不同的“记忆系统”——Checkpointer 和 Store。

结合Java 的视角，这就是 HttpSession（会话缓存） 和 Redis/MySQL（全局数据库） 的区别。


# 核心对比：Checkpointer vs. Store

维度	        Checkpointer（检查点）	                     Store（存储）

存的是什么	    图运行的全局状态快照（State）	        你自己定义的键值对数据（Key-Value）
作用范围	    单次对话/单条线程（Thread）	             跨对话/跨线程（Cross-Thread）
记忆类型	    短期记忆（对话历史、下一步去哪）	    长期记忆（用户偏好、业务事实、共享知识）
怎么用	        在 invoke 时传入 thread_id	           在 Node 里通过 runtime.store 读写
Java 类比	    Redis 里的 Session	                        MySQL / MongoDB



# 拆解这两个“兄弟”
1. Checkpointer（短期/线程级记忆）
它的作用：记住张三（thread_id=123）刚才说了什么。如果大模型因为网络超时或者人工审批挂起了，下次带着 thread_id=123 回来，它能恢复现场。

怎么用：你在 compile 的时候挂上它，调用时传 config={"configurable": {"thread_id": "xxx"}}。
常用实现：InMemorySaver（内存）、PostgresSaver（生产级）。

2. Store（长期/跨线程级记忆）
它的作用：记住张三这个人喜欢吃什么。哪怕张三明天开了一个全新的对话（新的 thread_id），Agent 依然能通过 Store 查到他昨天的偏好。

怎么用：在 compile 时挂上 store，然后在节点的函数里手动读写（它不会像 Checkpointer 那样自动保存，必须你自己写代码存和取）。
常用实现：InMemoryStore（内存）。

# 实战代码（怎么把它们挂上去）
    python
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.store.memory import InMemoryStore
    from langgraph.graph import StateGraph

    # 1. 实例化两个记忆系统
    checkpointer = InMemorySaver() # 存短期会话
    store = InMemoryStore()        # 存长期数据

    # 2. 编译图的时候，把它们都挂上去
    graph = builder.compile(checkpointer=checkpointer, store=store)

    # 3. 调用时，指定 thread_id（告诉系统看哪个 Session）
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Hi, my name is Bob."}]},
        {"configurable": {"thread_id": "thread-1"}}
    )


# 生产环境必踩的 4 个坑

PostgresSaver 的 thread_id 超长报错：
    数据库里存 thread_id 的字段是有长度限制的（通常是 255）。如果你的 thread_id 是用长字符串拼出来的，数据库会直接报错。解法：用 uuid 或者 MD5 哈希一下作为 thread_id。

MemorySaver 重启后数据全丢了：
    如果你用了 InMemorySaver，只要你的服务一重启，所有的历史对话全部清空。解法：生产环境必须用 PostgresSaver 或 SqliteSaver。

Checkpoints 无限膨胀，把数据库撑爆：
    用户每聊一句，Checkpointer 就会存一个快照。聊了 1000 句，数据库里就有 1000 个快照。解法：写个定时任务（Cron Job），定期把 N 天前的快照删掉（现在流行冷热数据分离）。

父图看不到子图的 Checkpoint：
    这就是你之前问过的那个问题的底层原因。子图有自己独立的 Checkpoint 命名空间，父图默认是看不到子图内部的。解法：跨图的数据共享，必须用 Store，或者用之前学的 Command.PARENT 越权写入。

总结
    要聊多轮对话、要支持断点续传（审批） -> 挂 Checkpointer。
    要记住用户的长期人设、偏好 -> 挂 Store。
    在本地测试，用 InMemory 开头的实现；线上，统统换 Postgres 开头的实现。

