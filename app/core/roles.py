from fastapi import Depends, HTTPException, status
from app.core.auth_utils import get_current_user
from typing import Callable, Tuple, Union

def require_role(*allowed_roles: str):
    """
    Verifica que el usuario autenticado tenga uno de los roles permitidos.

    Uso:
    @router.get("/")
    def endpoint(user: dict = require_role("admin")):
        ...
    """
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role")
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No role assigned in token"
            )
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role(s): {allowed_roles}"
            )
        return user
    return Depends(role_checker)
