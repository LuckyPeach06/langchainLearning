Checkpointer：管“这一次对话”（按 thread_id 隔离）。记得张三刚才说了什么。

Store：管“这个人”（按 user_id 或 namespace 隔离）。哪怕张三明天开一个全新的对话，Agent 依然能记得张三喜欢吃披萨。

# 核心概念：命名空间（Namespace）
Store 底层是一个巨大的 Key-Value 存储系统。

Namespace（命名空间）：一个元组（Tuple），相当于数据库里的表名或 Redis 里的前缀。通常按用户维度划分，比如 ("user_123", "memories")。

Key：相当于数据库的主键（比如 UUID）。

Value：你要存的数据，必须是一个字典（JSON 可序列化）。

# 基础读写操作
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

    # 1. 存记忆（Put）
    namespace = ("user_1", "memories")
    memory_id = "mem_001"
    memory_data = {"food_preference": "I like pizza"}
    store.put(namespace, memory_id, memory_data)

    # 2. 拿记忆（Search / Get）
    # 按前缀搜索，返回 Item 对象列表
    items = store.search(namespace)
    print(items[0].dict()) 
    # 输出: {'value': {'food_preference': 'I like pizza'}, 'key': 'mem_001', ...}

# 杀手锏功能：语义搜索（Semantic Search）
支持向量检索（RAG）。
在实例化 Store 时，传入 Embedding 模型和维度：

    from langchain.embeddings import init_embeddings

    store = InMemoryStore(
        index={
            "embed": init_embeddings("openai:text-embedding-3-small"),
            "dims": 1536,
            "fields": ["food_preference", "$"] # 指定哪些字段需要被向量化
        }
    )
    然后，你可以直接用自然语言去搜：
    # 搜：“用户喜欢吃什么？”
    memories = store.search(
        namespace, 
        query="What does the user like to eat?", 
        limit=3
    )

# 如何在 Node 里使用 Store？（核心代码）
不需要手动把 store 像普通参数一样传进去。只要挂载了它，LangGraph 会在底层自动注入 runtime 变量，直接从里面拿 store 和用户 ID 即可。

    from langgraph.runtime import Runtime
    from dataclasses import dataclass

    # 1. 定义运行期上下文（用来拿 user_id）
    @dataclass
    class Context:
        user_id: str

    # 2. 在节点里注入 Runtime
    async def call_model(state: MessagesState, runtime: Runtime[Context]):
        # 获取用户 ID
        user_id = runtime.context.user_id
        
        # 获取 Store 并搜索记忆
        namespace = (user_id, "memories")
        memories = await runtime.store.asearch(
            namespace, 
            query=state["messages"][-1].content, 
            limit=3
        )
        
        # 把搜出来的记忆拼到 Prompt 里
        info = "\n".join([d.value["memory"] for d in memories])
        # ... 拼给大模型 ...

# 生产环境 3 个坑
1. namespace 是“前缀匹配”！
文档里特别强调：如果你搜索 ("alice",)，它不仅会返回 ("alice", "memories") 的数据，还会返回 ("alice", "preferences") 的数据。如果你只想搜特定的，一定要传完整。

2. limit 截断是“静默的”！
如果你不传 limit，默认只返回 10 条。超出的部分不会报错，直接默默丢弃。如果数据多，必须自己写分页（用 offset）。

3. 永远不要在线上用 InMemoryStore
跟 Checkpointer 一样，测试可以，生产环境绝对不行（重启就丢）。线上请换成 PostgresStore、RedisStore 或 MongoDBStore。
