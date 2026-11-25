from langchain.tools import tool


@tool("web_search")  # 自定义名称
def search(query: str) -> str:
    """在网络上搜索信息。"""
    return f"Results for: {query}"

print(search.name)  # web_search

# 自定义工具描述
@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))






