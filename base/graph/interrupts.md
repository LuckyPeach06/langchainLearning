# 核心机制：interrupt() 到底是怎么暂停的？
它不是像 Java 的 Thread.sleep() 那样让线程原地挂起。

它的底层原理是：抛出一个特殊异常（Exception）。
当代码跑到 interrupt("请审批") 时，LangGraph 会抛出一个异常，把执行栈直接掀翻。引擎捕获到这个异常后，把当前状态（State）存档（Checkpoint），然后把图挂起。

最反直觉的一点（极其重要）：
当你传入 Command(resume="同意") 恢复执行时，LangGraph 并不是“原地苏醒”，而是从当前节点的第一行代码开始“重头重放（Replay）”！

interrupt() 的返回值，就是你在 resume 里传进去的值。

def approval_node(state):
    print("A 被执行了") # 每次 resume 都会打印
    decision = interrupt("同意吗？") # 第二次跑的时候，这里直接返回 "同意"，不再抛出异常
    return {"status": decision}


# 四大铁律
1. 绝对不能用 try...except Exception 包住 interrupt()
interrupt() 是靠抛出异常来暂停的。如果你写了个巨大的 try-catch，就会把暂停信号吃掉，导致图直接崩溃。只能用具体的异常（比如 except NetworkError）。

2. 节点内的 interrupt() 顺序绝对不能变
因为恢复时的值，是按位置索引（Index）一一对应的。如果你在节点里写了三个 interrupt()，恢复时传了三个值，它会严格按照第 1 个、第 2 个、第 3 个的顺序去匹配。如果你用 if-else 导致某次跳过了某个 interrupt()，序号就会全部错乱。

3. 别传复杂的对象
interrupt() 的参数必须能被序列化成 JSON（比如字典、字符串）。别传 Python 的类实例或函数，否则存 Checkpoint 时会报错。

4. 终极红线：interrupt() 之前的副作用必须幂等
因为恢复时会从头跑，如果你在 interrupt() 之前写了 db.create_log()，每次恢复都会重新执行一次，导致数据库里多出无数条废日志。
解法：任何写数据库、发邮件的动作，必须放在 interrupt() 之后，或者保证这个动作是幂等的（比如用 upsert）。

# 企业级高阶用法
1. 多个并发中断怎么恢复？
如果你的图并发跑了两个分支 A 和 B，两个分支都触发了 interrupt()。恢复时你不能只传一个值，必须传一个Map（字典），以 interrupt.id 为 Key 去对应：
resume_map = {
    "interrupt_A的ID": "A的答案",
    "interrupt_B的ID": "B的答案"
}
graph.invoke(Command(resume=resume_map), config)

2. 如何优雅地做“表单校验”？
如果你想做一个“如果用户输错，就重新让他输入”的死循环，千万不要在节点里写 while True（因为会无限重放报错）。
正确做法：
每次节点只执行一次 interrupt()，如果校验不通过，就把错误提示更新到 State 里，然后用条件边（Conditional Edge）把箭头指回自己，让它重新进节点。

3. 在 Tool（工具）内部使用
你可以把 interrupt() 直接写在 @tool 函数的代码里。这样当大模型决定调用这个工具时，就会自动触发审批弹窗，人类可以在恢复时直接修改工具的参数（比如修改发送邮件的收件人），然后再真正执行。

# 静态断点 vs 动态中断
动态中断（interrupt()）：写在代码逻辑里，可以精准控制什么时候暂停。生产环境做 HITL 必须用这个。

静态断点（interrupt_before / interrupt_after）：在编译或运行图的时候，强制在某些节点前后暂停。这个只用于本地开发调试（IDE里的单步调试），千万别用在生产环境。
