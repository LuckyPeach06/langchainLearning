import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


load_dotenv()


"""
    官网代码，由于deepseek不支持这种格式，所以执行失败
"""

os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")
llm = init_chat_model(f"openai:{os.getenv('LLM_MODEL_ID')}")


class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(description="The title of the movie")
    year: int = Field(description="The year the movie was released")
    director: str = Field(description="The director of the movie")
    rating: float = Field(description="The movie's rating out of 10")


model_with_structure = llm.with_structured_output(Movie)

response = model_with_structure.invoke("Provide details about the movie Inception")

print(response)  



# token的使用情况
# 许多模型提供商会在调用响应中返回 token 使用信息。
# 如果可用，该信息将包含在相应模型生成的 AIMessage 对象上
from langchain_core.callbacks import UsageMetadataCallbackHandler

callback = UsageMetadataCallbackHandler()
result_1 = llm.invoke("Hello", config={"callbacks": [callback]})
print(callback.usage_metadata)
# Output：
#{
#     'gpt-5.4-mini': {
#         'input_tokens': 8,
#         'output_tokens': 10,
#         'total_tokens': 18,
#         'input_token_details': {'audio': 0, 'cache_read': 0},
#         'output_token_details': {'audio': 0, 'reasoning': 0}
#     },
#     'claude-haiku-4-5-20251001': {
#         'input_tokens': 8,
#         'output_tokens': 21,
#         'total_tokens': 29,
#         'input_token_details': {'cache_read': 0, 'cache_creation': 0}
#     }
# }