Event Streaming = Agent Runtime 的类型化事件观察层。
它把模型文本、工具调用、状态变化、子智能体输出和自定义业务事件，拆成可订阅、可组合、可审计的 projection。

tream_events(..., version="v3") 不是 stream() 的简单替代，而是把 Agent 的运行过程提升成更清晰的工程接口：

stream.messages()：看模型消息、文本、推理片段和工具调用。
stream.tool_calls()：专门看工具调用输入与输出。
stream.values()：看每一步 state 的完整快照。
stream.output()：只关心最终输出。
stream.subagents() / stream.subgraphs()：区分复杂运行结构里的来源。
stream.interleave(...)：把多个投影重新合成一个有类型的事件流。
raw protocol 和 custom transformer：在默认投影不够时，自己定义观察方式。


简单来说，就是让 Agent 在后台干活的时候，随时给前端“报进度”

#  Event Streaming（事件流）：它到底解决什么问题
vent Streaming 解决的是“Agent 运行时如何被结构化观察”，而不是只解决“模型输出如何逐字显示”。

传统流式输出更像这样：
用户输入 -> 模型生成 -> token token token -> 最终文本

事件流更像这样：
用户输入 -> Agent runtime -> typed projections -> UI / Logs / Audit / Debug

区别在于，事件流不会把所有运行信号压扁成字符串。它会把不同类型的运行信息拆出来，让应用可以按需订阅。

Streaming 让你看到输出过程，Event Streaming 让你按类型理解运行过程。



# Projection（投影）：从原始事件里只取自己需要的视角
Projection 解决的是“同一段 Agent 运行过程，不同消费者应该看到不同形态的数据”。

一个 Agent 运行时会产生很多底层事件：模型开始、模型 token、工具调用、工具返回、状态更新、子图运行、自定义事件等。前端、日志系统、调试器不应该都处理同一堆原始事件。

所以官方文档提供了多种投影方法，把底层事件转换成更好用的对象：

投影方法	                中文理解	                常见用途
stream.messages()	        消息投影	            聊天 UI、token 展示、工具调用片段
stream.tool_calls()	        工具调用投影	        工具审计、参数展示、调用结果追踪
stream.values()	            状态值投影	            调试 Agent state、观察每步状态
stream.output()	            最终输出投影	        只拿最后结果
stream.events()	            原始事件协议	        自定义解析、底层诊断
stream.interleave(...)	    多投影交错	            同时消费多种事件

可以把它理解为数据的不同视图。底层是同一股事件流，但 LangChain 帮你按维度切分成了不同的流。
前端想要文字，就监听 stream.messages；想展示“正在调用工具”的 UI，就监听 stream.tool_calls。

# 工程落地：前端、后端和审计系统怎么分工

可以把事件流按消费者分成几层：

消费者	            推荐投影	                                 主要目的
聊天前端	        messages()	                       展示回答文本、推理片段、工具调用提示
工具面板	        tool_calls()	                        展示工具名、参数、结果
调试控制台	        values() / events()	                 查看状态变化和底层事件
多 Agent 界面	  subagents() / subgraphs()	                     区分事件来源
后台任务	        output()	                                获取最终结果
统一日志	     interleave(...) / custom transformer	    保留完整时间线并转成内部协议
