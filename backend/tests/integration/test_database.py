from __future__ import annotations

import pytest
from uuid import uuid4

from backend.app.models.db.conversation import Conversation, Approval
from backend.app.repositories.conversation import ConversationRepository, MessageRepository
from backend.app.repositories.approval import ApprovalRepository


@pytest.fixture
async def session():
    from backend.app.core.database import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        yield session


@pytest.fixture
def conversation_repo(session):
    return ConversationRepository(session)


@pytest.fixture
def message_repo(session):
    return MessageRepository(session)


@pytest.fixture
def approval_repo(session):
    return ApprovalRepository(session)


def new_uuid():
    return str(uuid4())


@pytest.mark.asyncio
async def test_create_conversation(conversation_repo: ConversationRepository):
    conv_id = new_uuid()
    conv = Conversation(id=conv_id, customer_id="C001", status="active")
    result = await conversation_repo.create(conv)
    assert result.id == conv_id
    assert result.customer_id == "C001"
    assert result.status == "active"


@pytest.mark.asyncio
async def test_get_conversation_by_id(conversation_repo: ConversationRepository):
    conv_id = new_uuid()
    conv = Conversation(id=conv_id, customer_id="C002", status="active")
    await conversation_repo.create(conv)
    result = await conversation_repo.get_by_id(conv_id)
    assert result is not None
    assert result.customer_id == "C002"


@pytest.mark.asyncio
async def test_get_conversations_by_customer(conversation_repo: ConversationRepository):
    c_id = new_uuid()
    conv1 = Conversation(id=new_uuid(), customer_id=c_id, status="active")
    conv2 = Conversation(id=new_uuid(), customer_id=c_id, status="resolved")
    await conversation_repo.create(conv1)
    await conversation_repo.create(conv2)
    results = await conversation_repo.get_by_customer(c_id)
    assert len(results) >= 2


@pytest.mark.asyncio
async def test_update_conversation_status(conversation_repo: ConversationRepository):
    conv_id = new_uuid()
    conv = Conversation(id=conv_id, customer_id="C004", status="active")
    await conversation_repo.create(conv)
    updated = await conversation_repo.update_status(conv_id, "resolved")
    assert updated is not None
    assert updated.status == "resolved"


@pytest.mark.asyncio
async def test_create_message(message_repo: MessageRepository):
    msg = await message_repo.create_message(
        conversation_id=new_uuid(), role="user", content="Hello"
    )
    assert msg.role == "user"
    assert msg.content == "Hello"


@pytest.mark.asyncio
async def test_get_messages_by_conversation(message_repo: MessageRepository):
    conv_id = new_uuid()
    await message_repo.create_message(conversation_id=conv_id, role="user", content="Msg1")
    await message_repo.create_message(conversation_id=conv_id, role="assistant", content="Msg2")
    messages = await message_repo.get_by_conversation(conv_id)
    assert len(messages) >= 2


@pytest.mark.asyncio
async def test_create_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id=new_uuid(),
        approval_type="refund_approval",
        customer_id="C001",
        agent_name="refund",
        action_description="Process refund",
        risk_level="high",
    )
    assert approval.status == "pending"
    assert approval.risk_level == "high"


@pytest.mark.asyncio
async def test_approve_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id=new_uuid(),
        approval_type="refund_approval",
        customer_id="C005",
        agent_name="refund",
        action_description="Process refund",
    )
    result = await approval_repo.approve(approval.id, "admin", "Approved")
    assert result is not None
    assert result.status == "approved"
    assert result.decided_by == "admin"


@pytest.mark.asyncio
async def test_reject_approval(approval_repo: ApprovalRepository):
    approval = await approval_repo.create_approval(
        conversation_id=new_uuid(),
        approval_type="refund_approval",
        customer_id="C006",
        agent_name="refund",
        action_description="Process refund",
    )
    result = await approval_repo.reject(approval.id, "admin", "Rejected")
    assert result is not None
    assert result.status == "rejected"


@pytest.mark.asyncio
async def test_get_pending_approvals(approval_repo: ApprovalRepository):
    await approval_repo.create_approval(
        conversation_id=new_uuid(),
        approval_type="refund_approval",
        customer_id="C007",
        agent_name="refund",
        action_description="Process refund",
    )
    pending = await approval_repo.get_pending()
    assert len(pending) >= 1
    assert all(a.status == "pending" for a in pending)
