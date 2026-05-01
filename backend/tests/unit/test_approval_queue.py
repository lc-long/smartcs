from __future__ import annotations

import pytest
from backend.app.services.approval_queue import ApprovalItem, ApprovalQueue, get_approval_queue


class TestApprovalQueue:
    def setup_method(self):
        self.queue = ApprovalQueue()

    def test_add_and_get(self):
        item = ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款800元",
        )
        self.queue.add(item)
        assert self.queue.count_pending() == 1

        retrieved = self.queue.get(str(item.id))
        assert retrieved is not None
        assert retrieved.conversation_id == "conv-1"
        assert retrieved.status == "pending"

    def test_approve(self):
        item = ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款800元",
        )
        self.queue.add(item)

        result = self.queue.approve(str(item.id), resolved_by="admin", comment="同意")
        assert result is not None
        assert result.status == "approved"
        assert result.resolved_by == "admin"
        assert self.queue.count_pending() == 0

    def test_reject(self):
        item = ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款800元",
        )
        self.queue.add(item)

        result = self.queue.reject(str(item.id), resolved_by="admin", comment="不符合条件")
        assert result is not None
        assert result.status == "rejected"
        assert self.queue.count_pending() == 0

    def test_get_pending(self):
        for i in range(3):
            self.queue.add(ApprovalItem(
                conversation_id=f"conv-{i}",
                approval_type="refund_approval",
                customer_id=f"C{i}",
                agent_name="refund",
                action_description=f"退款{i*100}元",
            ))

        assert self.queue.count_pending() == 3
        assert len(self.queue.get_pending()) == 3

    def test_get_by_conversation(self):
        self.queue.add(ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款500元",
        ))
        self.queue.add(ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款800元",
        ))
        self.queue.add(ApprovalItem(
            conversation_id="conv-2",
            approval_type="refund_approval",
            customer_id="C002",
            agent_name="refund",
            action_description="退款300元",
        ))

        items = self.queue.get_by_conversation("conv-1")
        assert len(items) == 2

    def test_cannot_approve_twice(self):
        item = ApprovalItem(
            conversation_id="conv-1",
            approval_type="refund_approval",
            customer_id="C001",
            agent_name="refund",
            action_description="退款800元",
        )
        self.queue.add(item)

        self.queue.approve(str(item.id), resolved_by="admin")
        result = self.queue.approve(str(item.id), resolved_by="admin2")
        assert result is None

    def test_nonexistent_approval(self):
        result = self.queue.get("nonexistent-id")
        assert result is None

        result = self.queue.approve("nonexistent-id", resolved_by="admin")
        assert result is None
