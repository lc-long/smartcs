import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage
from backend.app.services.llm.provider import get_llm_provider

PROMPT = """分析用户消息，判断意图类别。
意图类别（必须使用以下英文值）：
- billing: 账单相关
- technical: 技术支持
- refund: 退款相关
- escalation: 用户明确要求人工客服
- general: 其他无法分类的问题
请直接输出JSON：{"intent": "billing", "confidence": 0.9, "reasoning": "理由"}"""


async def test():
    provider = get_llm_provider()
    llm = provider.get_llm(model_name="MiniMax-M2.7", temperature=0.0)
    messages = [SystemMessage(content=PROMPT), HumanMessage(content="我想查账单")]
    resp = await llm.ainvoke(messages)
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    first = content.find("{")
    last = content.rfind("}")
    if first != -1 and last != -1:
        data = json.loads(content[first : last + 1])
        print(f"Intent: {data.get('intent')}")
        print(f"Confidence: {data.get('confidence')}")


asyncio.run(test())
