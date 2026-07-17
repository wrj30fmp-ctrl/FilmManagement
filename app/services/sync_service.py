"""
同步服务（预留接口）

第一阶段不实现云同步功能，仅保留接口定义。
未来增加云端同步时，这些方法将被实现。
"""

import logging

logger = logging.getLogger(__name__)


class SyncService:
    """同步服务 - 预留接口"""

    def __init__(self):
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """同步是否已启用"""
        return self._enabled

    def sync_all(self) -> dict:
        """执行完整同步（推送 + 拉取）

        Returns:
            {"success": bool, "message": str}
        """
        if not self._enabled:
            return {"success": False, "message": "云同步功能尚未启用。"}
        # TODO: 实现同步逻辑
        return {"success": False, "message": "同步功能将在后续版本中实现。"}

    def push_pending_changes(self) -> dict:
        """推送本地待同步的变更到云端"""
        if not self._enabled:
            return {"success": False, "message": "云同步功能尚未启用。"}
        return {"success": False, "message": "推送功能将在后续版本中实现。"}

    def pull_remote_changes(self) -> dict:
        """从云端拉取远程变更"""
        if not self._enabled:
            return {"success": False, "message": "云同步功能尚未启用。"}
        return {"success": False, "message": "拉取功能将在后续版本中实现。"}

    def resolve_conflict(self, record_id: str, resolution: str) -> dict:
        """解决同步冲突

        Args:
            record_id: 冲突记录 UUID
            resolution: "keep_local" / "keep_remote" / "merge"

        Returns:
            {"success": bool, "message": str}
        """
        if not self._enabled:
            return {"success": False, "message": "云同步功能尚未启用。"}
        return {"success": False, "message": "冲突解决功能将在后续版本中实现。"}

    def mark_as_synced(self, record_ids: list[str]) -> bool:
        """将记录标记为已同步"""
        return True  # 第一阶段总是返回 True

    def mark_as_failed(self, record_ids: list[str]) -> bool:
        """将记录标记为同步失败"""
        return True
