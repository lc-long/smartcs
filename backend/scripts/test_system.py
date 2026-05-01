"""System Test Script"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

BASE_URL = "http://localhost:8000"


async def login(username: str, password: str) -> str:
    """Login and get token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        else:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return None


async def chat(token: str, message: str, customer_id: str = None) -> dict:
    """Send chat message"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "customer_id": customer_id or "C001",
                "message": message,
            },
            headers=headers,
            timeout=180.0,  # 3 minutes for complex tasks
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"{resp.status_code}: {resp.text}"}


async def test_scenario(name: str, token: str, message: str, customer_id: str = None):
    """Test single scenario"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Message: {message}")
    print(f"Customer: {customer_id or 'C001'}")
    print("-"*60)

    result = await chat(token, message, customer_id)

    if "error" in result:
        print(f"[FAIL] Error: {result['error']}")
    else:
        agent = result.get("metadata", {}).get("model_used", "unknown")
        intent = result.get("metadata", {}).get("intent", "unknown")
        content = result.get("message", {}).get("content", "")

        # Remove all non-ASCII characters for console output
        content_clean = content.encode('ascii', 'ignore').decode('ascii')

        print(f"Agent: {agent}")
        print(f"Intent: {intent}")
        print(f"Response:\n{content_clean[:500]}")

    return result


async def main():
    print("="*60)
    print("SmartCS System Test")
    print("="*60)

    # 1. Login test
    print("\n[1] Login Test")
    token = await login("zhangsan", "zhangsan123")
    if not token:
        print("[FAIL] Login failed, cannot continue")
        return
    print(f"[OK] Login success, token: {token[:20]}...")

    # 2. Basic function tests
    await test_scenario(
        "Query Orders",
        token,
        "Help me check my orders",
        "C001",
    )

    await test_scenario(
        "Query Billing",
        token,
        "What is my billing status?",
        "C001",
    )

    await test_scenario(
        "Query Refund Status",
        token,
        "Do I have any refund requests?",
        "C001",
    )

    # 3. Multi-turn dialogue test
    await test_scenario(
        "Multi-turn - Refund Query",
        token,
        "Refund",
        "C001",
    )

    # 4. Complex task test
    await test_scenario(
        "Complex Task - Refund + Billing",
        token,
        "My smart watch Pro has screen flickering issues, I want a refund. Also, I think my billing last month was overcharged, please check.",
        "C001",
    )

    # 5. Sentiment test
    await test_scenario(
        "Sentiment - Negative",
        token,
        "I am very angry! Your service is terrible! I want to complain!",
        "C001",
    )

    # 6. Data isolation test
    await test_scenario(
        "Data Isolation - Other Customer",
        token,
        "Help me check customer C002 orders",
        "C001",
    )

    # 7. Agent account test
    print("\n" + "="*60)
    print("Switch to Agent Account")
    print("="*60)

    agent_token = await login("agent1", "agent123")
    if agent_token:
        print(f"[OK] Agent login success")

        await test_scenario(
            "Agent - View All Orders",
            agent_token,
            "Help me check all orders",
            None,
        )
    else:
        print("[FAIL] Agent login failed")

    # 8. Admin account test
    print("\n" + "="*60)
    print("Switch to Admin Account")
    print("="*60)

    admin_token = await login("admin", "admin123")
    if admin_token:
        print(f"[OK] Admin login success")

        await test_scenario(
            "Admin - View Refunds",
            admin_token,
            "Help me check refund requests",
            None,
        )
    else:
        print("[FAIL] Admin login failed")

    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
