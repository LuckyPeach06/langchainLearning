role 和 content 组织模型看到的上下文
metadata 与 AIMessage 的返回字段则留给程序判断下一步

# role、content 和 metadata 分别管什么
role 决定这条信息以什么身份进入上下文
content 是真正的消息载荷
metadata 服务程序，而不是用来偷偷扩写提示词

# content_blocks 是标准视图，不是新的供应商能力
Message 的 content 很灵活。
官方文档列出了三种常见形态：字符串、供应商原生内容块列表，以及 LangChain 标准内容块列表。
灵活让不同模型能力能够进入同一个 Message 接口，也意味着直接读取原始 content 时可能遇到不同结构。

content_blocks 提供标准、类型化的读取视图。
它会尝试把原始 content 解析成统一的文本、推理、图片、音频、文件或工具调用等块；
创建 Message 时，也可以直接传入标准块。


from langchain.messages import HumanMessage

message = HumanMessage(
    content_blocks=[
        {"type": "text", "text": "请概括这份天气报告。"},
        {
            "type": "file",
            "url": "https://example.com/beijing-weather.pdf",
            "mime_type": "application/pdf",
        },
    ]
)

print(message.content)
print(message.content_blocks)


官方文档列了很多内容块类型。对于工程落地，可以先记住这几组：

类型	                     中文解释	                   常见用途

TextContentBlock	        文本内容块	                普通回答、提示词、摘要
ReasoningContentBlock	    推理内容块	                模型推理摘要或思考过程
ImageContentBlock	        图片内容块	                图片理解、商品识别、截图分析
AudioContentBlock	        音频内容块	                语音输入、录音理解
VideoContentBlock	        视频内容块	                视频片段理解
FileContentBlock	        文件内容块	                PDF、文档、附件
ToolCall	                工具调用块	                模型请求调用函数
ToolCallChunk	            工具调用流式片段	        流式生成工具参数
InvalidToolCall	            无效工具调用	            捕获 JSON 解析失败等异常
ServerToolCall	            服务端工具调用	            供应商侧执行的工具请求
ServerToolResult	        服务端工具结果	            供应商侧工具执行结果
NonStandardContentBlock	    非标准内容块	            供应商特有结构兜底
