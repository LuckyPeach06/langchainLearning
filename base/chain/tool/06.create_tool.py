from langchain.tools import tool

# 创建工具
# 类型提示（Type hints）是必需的
# 建议使用 snake_case 命名工具，部分模型提供商对包含空格或特殊字符的名称存在兼容性问题，或会直接报错
@tool
def search_database(query: str, limit: int = 10) -> str:
    """在客户数据库中搜索与查询匹配的记录。

    Args:
        query: 要查找的搜索词
        limit: 返回结果的最大数量
    """
    return f"Found {limit} results for '{query}'"


# 自定义工具
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

# 高级定义
# 使用 Pydantic 模型或 JSON 模式定义复杂输入

from pydantic import BaseModel, Field
from typing import Literal

class WeatherInput(BaseModel):
    """天气查询的输入。"""
    location: str = Field(description="城市名称或坐标")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="温度单位偏好"
    )
    include_forecast: bool = Field(
        default=False,
        description="是否包含5天预报"
    )

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """获取当前天气及可选预报。"""
    temp = 22 if units == "celsius" else 72
    result = f"{location} 的当前天气：{temp} 度 {units[0].upper()}"
    if include_forecast:
        result += "\n未来5天：晴朗"
    return result

# 保留参数名
# 以下参数不能用作工具参数

# 参数名	用途
# config	保留用于在内部将 RunnableConfig 传递给工具
# runtime	保留用于 ToolRuntime 参数（访问状态、上下文、存储）