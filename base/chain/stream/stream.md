Streaming = Runtime Feedback Channel。
它把 Agent 从“黑盒等待”变成“可观察、可交互、可恢复的实时运行过程”。



Streaming 主要解决三件事：

updates：让应用看到 Agent 每一步状态变化。
messages：让应用看到模型 token、推理片段和工具调用分片。
custom：让业务工具主动发出自定义进度。

# stream_mode（流模式）：三种信号不要混在一起
stream_mode 解决的是“你到底想看哪一种实时信号”

stream_mode	        中文理解	            适合看什么
updates	           状态更新流	    Agent 每一步完成后的状态，例如模型节点、工具节点、最终回复
messages	      消息 token        LLM token、工具调用分片、消息元数据
custom	          自定义业务流	    工具内部主动上报的业务进度，例如已读取多少条记录

stream_mode 是订阅开关：想看状态用 updates，想看 token 用 messages，想看业务进度用 custom

# Agent 不是一次性函数调用，而是一段正在运行的过程。Streaming 就是这段过程对外暴露的实时反馈层。

层次	        关键对象	                                            你在看什么
用户体验层	    messages	                                模型 token、推理片段、工具调用分片
执行状态层	    updates	model                                    节点、tools 节点、最终回复
业务进度层	    custom、get_stream_writer                           	工具内部的业务进度
生产治理层	thread_id、checkpointer、interrupt、lc_agent_name	恢复、审核、多 Agent 来源识别

Streaming 让 Agent 的运行过程可见；可见之后，前端才能展示，后台才能审计，人才能在关键时刻介入。