"""创建默认用户"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.database import get_engine, init_db
from backend.app.core.security import get_password_hash
from backend.app.models.db.user import User
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

        # 创建默认用户
        users = [
            User(
                username="admin",
                email="admin@smartcs.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                role="admin",
                is_active=True,
            ),
            User(
                username="agent1",
                email="agent1@smartcs.com",
                hashed_password=get_password_hash("agent123"),
                full_name="客服小王",
                role="agent",
                is_active=True,
            ),
            User(
                username="viewer",
                email="viewer@smartcs.com",
                hashed_password=get_password_hash("viewer123"),
                full_name="访客用户",
                role="viewer",
                is_active=True,
            ),
        ]

        for user in users:
            session.add(user)

        await session.commit()

        print("[OK] Default users created:")
        print("  - admin / admin123 (Admin)")
        print("  - agent1 / agent123 (Agent)")
        print("  - viewer / viewer123 (Viewer)")


if __name__ == "__main__":
    asyncio.run(create_default_users())
