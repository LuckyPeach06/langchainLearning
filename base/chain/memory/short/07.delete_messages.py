# 要从图状态中删除消息，可以使用 RemoveMessage。

# 要使 RemoveMessage 生效，您需要使用带有 add_messages reducer 的状态键。

# 默认的 AgentState 已提供此功能。

from langchain.messages import RemoveMessage  

def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # 移除最早的两条消息
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}  