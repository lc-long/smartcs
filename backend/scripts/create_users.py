"""创建默认用户"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.database import get_engine, init_db
from backend.app.core.security import get_password_hash
from backend.app.models.db.user import User
from backend.app.models.db.ecommerce import Customer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text


async def create_default_users():
    """创建默认用户"""
    engine = get_engine()
    await init_db()

    async with AsyncSession(engine) as session:
        # 清空用户表
        await session.execute(text("DELETE FROM users"))
        await session.commit()

        # 查询现有客户
        result = await session.execute(select(Customer))
        customers = {c.name: c.id for c in result.scalars()}
        print(f"Found customers: {customers}")

        # 创建默认用户
        users = [
            User(
                username="admin",
                email="admin@smartcs.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                role="admin",
                customer_id=None,  # 管理员不关联客户
                is_active=True,
            ),
            User(
                username="agent1",
                email="agent1@smartcs.com",
                hashed_password=get_password_hash("agent123"),
                full_name="客服小王",
                role="agent",
                customer_id=None,  # 客服不关联客户
                is_active=True,
            ),
            User(
                username="zhangsan",
                email="zhangsan@example.com",
                hashed_password=get_password_hash("zhangsan123"),
                full_name="张三",
                role="viewer",
                customer_id=customers.get("张三"),  # 关联到客户C001
                is_active=True,
            ),
            User(
                username="lisi",
                email="lisi@example.com",
                hashed_password=get_password_hash("lisi123"),
                full_name="李四",
                role="viewer",
                customer_id=customers.get("李四"),  # 关联到客户C002
                is_active=True,
            ),
        ]

        for user in users:
            session.add(user)

        await session.commit()

        print("[OK] Default users created:")
        print("  - admin / admin123 (Admin, no customer)")
        print("  - agent1 / agent123 (Agent, no customer)")
        print("  - zhangsan / zhangsan123 (Viewer, customer C001)")
        print("  - lisi / lisi123 (Viewer, customer C002)")


if __name__ == "__main__":
    asyncio.run(create_default_users())
