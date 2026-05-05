# ============================================================================
# 单Agent架构 - 此文件已重构，使用 ServiceWorkflow 替代
# 旧的多Agent架构已移至 customer_service_backup.py
# ============================================================================

from backend.app.workflows.service_workflow import ServiceWorkflow, get_workflow

__all__ = ["ServiceWorkflow", "get_workflow"]
