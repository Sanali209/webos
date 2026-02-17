from functools import wraps
from typing import List, Callable

from fastapi import HTTPException, status, Depends
from src.core.auth import current_active_user, User

def require_permission(permission: str):
    """
    Dependency that checks if the current user has the specified permission.
    """
    def decoder(user: User = Depends(current_active_user)):
        if permission not in user.permissions and user.role != "admin":
            from loguru import logger
            logger.warning(f"User {user.id} denied access to permission: {permission}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    return decoder
