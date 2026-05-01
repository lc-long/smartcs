from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.db.conversation import Conversation, Message, Approval
from backend.app.repositories.conversation import ConversationRepository, MessageRepository
from backend.app.repositories.approval import ApprovalRepository


@pytest.fixture
async def session():
    from backend.app.core.database import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def conversation_repo(session: AsyncSession):
    return ConversationRepository(session)


@pytest.fixture
def message_repo(session: AsyncSession):
    return MessageRepository(session)


@pytest.fixture
def approval_repo(session: AsyncSession):
    return ApprovalRepository(session)


async def test_create_conversation(conversation_repo: ConversationRepository):
    conv = Conversation(
        id="test-conv-1",
        customer_id="C001",
        status="active",
    )
    result = await conversation_repo.create(conv)
    assert result.id == "test-conv-1"
    assert result.customer_id == "C001"
    assert result.status == "active"


async def test_get_conversation_by_id(conversation_repo: ConversationRepository):
    conv = Conversation(
        id="test-conv-2",
        customer_id="C002",
        status="active",
    )
    await conversation_repo.create(conv)
    result = await conversation_repo.get_by_id("test-conv-2")
    assert result is not None
    assert result.customer_id == "C002"


async def test_get_conversations_by_customer(conversation_repo: ConversationRepository):
    conv1 = Conversation(id="test-conv-3", customer_id="C003", status="active")
    conv2 = Conversation(id="test-conv-4", customer_id="C003", status="resolved")
    await conversation_repo.create(conv1)
    await conversation_repo.create(conv2)

    results = await conversation_repo.get_by_customer("C003")
    assert len(results) >= 2


async def test_update_conversation_status(conversation_repo: ConversationRepository):
    conv = Conversation(id="test-conv-5", customer_id="C004", status="active")
    await conversation_repo.create(conv)
    updated = await conversation_repo.update_status("test-conv-5", "resolved")
    assert updated is not None
    assert updated.status == "resolved"


async def test_create_message(message_repo: MessageRepository):
    msg = await message_repo.create_message(
        conversation_id="test-conv-1",
        role="user",
        content="Hello",
    )
    assert msg.role == "user"
    assert msg.content == "Hello"


async def test_get_messages_by_conversation(message_repo: MessageRepository):
    await message_repo.create_message(
        conversation_id="test-conv-6",
        role="user",
        content="Message 1",
    )
    await message_repo.create_message(
        conversation_id="test-conv-6",
        role="assistant",
        content="Response 1",
    )

    messages = await message_repo.get_by_conversation("test-conv-6")
    assert len(messages) >= 2


async def test_create_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id="test-conv-1",
        approval_type="refund_approval",
        customer_id="C001",
        agent_name="refund",
        action_description="Process refund of 500",
        risk_level="high",
    )
    assert approval.status == "pending"
    assert approval.risk_level == "high"


async def test_approve_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id="test-conv-7",
        approval_type="refund_approval",
        customer_id="C005",
        agent_name="refund",
        action_description="Process refund",
    )
    result = await approval_repo.approve(approval.id, "admin", "Approved for testing")
    assert result is not None
    assert result.status == "approved"
    assert result.decided_by == "admin"


async def test_reject_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id="test-conv-8",
        approval_type="refund_approval",
        customer_id="C006",
        agent_name="refund",
        action_description="Process refund",
    )
    result = await approval_repo.reject(approval.id, "admin", "Insufficient documentation")
    assert result is not None
    assert result.status == "rejected"


async def test_get_pending_approvals(approval_repo: ApprovalRepository):
    await approval_repo.create_approval(
        conversation_id="test-conv-9",
        approval_type="refund_approval",
        customer_id="C007",
        agent_name="refund",
        action_description="Process refund",
    )
    pending = await approval_repo.get_pending()
    assert len(pending) >= 1
    assert all(a.status == "pending" for a in pending)
