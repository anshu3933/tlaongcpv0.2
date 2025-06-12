from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.audit_log import AuditLog

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        user_id: int,
        user_role: str,
        ip_address: str,
        details: Optional[dict] = None
    ) -> AuditLog:
        try:
            audit_log = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                user_role=user_role,
                ip_address=ip_address,
                details=details
            )
            self.session.add(audit_log)
            await self.session.commit()
            await self.session.refresh(audit_log)
            return audit_log
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_logs_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        try:
            result = await self.session.execute(
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.entity_type == entity_type,
                        AuditLog.entity_id == entity_id
                    )
                )
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_logs_by_user(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        try:
            result = await self.session.execute(
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            await self.session.rollback()
            raise e

 