from typing import Optional, List, Dict
from datetime import datetime, timedelta
from ..models.user import User
from ..models.user_session import UserSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_session_by_token(self, token_hash: str) -> Optional[UserSession]:
        """Get a user session by token hash"""
        try:
            result = await self.session.execute(
                select(UserSession).where(UserSession.token_hash == token_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise e

    async def get_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise e

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise e

    async def create(self, user: User) -> User:
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            raise e

    async def update(self, user: User) -> User:
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete(self, user_id: int) -> bool:
        try:
            user = await self.get_by_id(user_id)
            if user:
                await self.session.delete(user)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            raise e

    async def list_all(self) -> List[User]:
        try:
            result = await self.session.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            raise e

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID and return as dictionary"""
        try:
            user = await self.get_by_id(user_id)
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                }
            return None
        except Exception as e:
            raise e

    async def create_session(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        """Create a new user session"""
        try:
            session = UserSession(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            self.session.add(session)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        try:
            user = await self.get_by_id(user_id)
            if user:
                # Use func.now() to match server_default behavior with timezone
                user.last_login = func.now()
                await self.update(user)
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_users_by_role(self, role: str) -> List[Dict]:
        """Get all active users with a specific role"""
        try:
            result = await self.session.execute(
                select(User).where(
                    and_(
                        User.role == role,
                        User.is_active == True
                    )
                )
            )
            users = result.scalars().all()
            return [
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
                for user in users
            ]
        except Exception as e:
            raise e
        
    async def delete_expired_sessions(self) -> int:
        """Delete all expired sessions and return count of deleted sessions"""
        try:
            current_time = datetime.now()
            result = await self.session.execute(
                select(UserSession).where(
                    UserSession.expires_at < current_time
                )
            )
            expired_sessions = result.scalars().all()
            
            for session in expired_sessions:
                await self.session.delete(session)
                
            await self.session.commit()
            return len(expired_sessions)
        except Exception as e:
            await self.session.rollback()
            raise e
            
    async def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user and return count of deleted sessions"""
        try:
            result = await self.session.execute(
                select(UserSession).where(
                    UserSession.user_id == user_id
                )
            )
            user_sessions = result.scalars().all()
            
            for session in user_sessions:
                await self.session.delete(session)
                
            await self.session.commit()
            return len(user_sessions)
        except Exception as e:
            await self.session.rollback()
            raise e
        
    async def get_session_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Get a user session by token hash"""
        result = await self.session.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
        
    async def delete_expired_sessions(self) -> int:
        """Delete all expired sessions and return count of deleted sessions"""
        try:
            current_time = datetime.now()
            result = await self.session.execute(
                select(UserSession).where(UserSession.expires_at < current_time)
            )
            expired_sessions = result.scalars().all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                await self.session.delete(session)
            
            await self.session.commit()
            return count
        except Exception as e:
            await self.session.rollback()
            raise e
            
    async def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a specific user and return count of deleted sessions"""
        try:
            result = await self.session.execute(
                select(UserSession).where(UserSession.user_id == user_id)
            )
            user_sessions = result.scalars().all()
            
            count = len(user_sessions)
            for session in user_sessions:
                await self.session.delete(session)
            
            await self.session.commit()
            return count
        except Exception as e:
            await self.session.rollback()
            raise e
