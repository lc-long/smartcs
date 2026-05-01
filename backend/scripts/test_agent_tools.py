"""测试 Agent function calling"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.services.llm.provider import get_llm_provider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """获取天气信息"""
    return f"{city}今天晴天，温度25度"


async def test():
    provider = get_llm_provider()
    llm = provider.get_llm(model_name="MiniMax-M2.7", temperature=0.3)

    # 测试1: 使用 bind_tools
    print("=" * 50)
    print("测试1: 使用 bind_tools")
    print("=" * 50)

    try:
        llm_with_tools = llm.bind_tools([get_weather])
        response = await llm_with_tools.ainvoke([
            SystemMessage(content="你是一个天气助手"),
            HumanMessage(content="北京今天天气怎么样？"),
        ])
        print(f"成功: {response.content[:200]}")
        print(f"tool_calls: {response.tool_calls}")
    except Exception as e:
        print(f"失败: {e}")

    # 测试2: 使用 invoke 并传入 tools
    print("\n" + "=" * 50)
    print("测试2: 使用 invoke 并传入 tools")
    print("=" * 50)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content="你是一个天气助手"),
                HumanMessage(content="北京今天天气怎么样？"),
            ],
            tools=[get_weather],
        )
        print(f"成功: {response.content[:200]}")
        print(f"tool_calls: {response.tool_calls}")
    except Exception as e:
        print(f"失败: {e}")


if __name__ == "__main__":
    asyncio.run(test())
