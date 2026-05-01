"""测试 MiniMax function calling 格式"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.config.settings import get_settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


async def test_function_calling():
    settings = get_settings()

    llm = ChatOpenAI(
        model="MiniMax-M2.7",
        temperature=0.3,
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
    )

    # 测试1: 不带 tools 的普通调用
    print("=" * 50)
    print("测试1: 普通调用（不带 tools）")
    print("=" * 50)

    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个助手"),
            HumanMessage(content="你好"),
        ])
        print(f"成功: {response.content[:100]}")
    except Exception as e:
        print(f"失败: {e}")

    # 测试2: 带 tools 的调用（OpenAI 格式）
    print("\n" + "=" * 50)
    print("测试2: 带 tools 的调用（OpenAI 格式）")
    print("=" * 50)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    ]

    try:
        llm_with_tools = llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke([
            SystemMessage(content="你是一个天气助手"),
            HumanMessage(content="北京今天天气怎么样？"),
        ])
        print(f"成功: {response.content[:100]}")
        print(f"tool_calls: {response.tool_calls}")
    except Exception as e:
        print(f"失败: {e}")

    # 测试3: 使用不同的 tools 格式
    print("\n" + "=" * 50)
    print("测试3: 使用 functions 格式（旧版 OpenAI）")
    print("=" * 50)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content="你是一个天气助手"),
                HumanMessage(content="北京今天天气怎么样？"),
            ],
            functions=[
                {
                    "name": "get_weather",
                    "description": "获取天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称",
                            }
                        },
                        "required": ["city"],
                    },
                }
            ],
        )
        print(f"成功: {response.content[:100]}")
    except Exception as e:
        print(f"失败: {e}")

    # 测试4: 直接用 HTTP 请求测试 MiniMax API
    print("\n" + "=" * 50)
    print("测试4: 直接 HTTP 请求测试")
    print("=" * 50)

    import httpx

    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }

    # 不带 tools
    payload = {
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"},
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.minimax_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"成功: {data['choices'][0]['message']['content'][:100]}")
            else:
                print(f"失败: {resp.text}")
    except Exception as e:
        print(f"失败: {e}")

    # 带 tools
    print("\n" + "=" * 50)
    print("测试5: 直接 HTTP 请求带 tools")
    print("=" * 50)

    payload_with_tools = {
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "system", "content": "你是一个天气助手"},
            {"role": "user", "content": "北京今天天气怎么样？"},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称",
                            }
                        },
                        "required": ["city"],
                    },
                },
            }
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.minimax_base_url}/chat/completions",
                headers=headers,
                json=payload_with_tools,
                timeout=30,
            )
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"成功: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            else:
                print(f"失败: {resp.text}")
    except Exception as e:
        print(f"失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_function_calling())
