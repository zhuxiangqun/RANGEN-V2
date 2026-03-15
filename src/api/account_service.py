"""
Account API - User authentication with bcrypt password encryption
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from src.services.account_service import get_account_service, UserRole, LoginResult

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    role: str = "user"
    email: Optional[str] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    ip_address: str = "unknown"
    user_agent: str = "unknown"


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    user_id: str
    old_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    user_id: str
    new_password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    role: str
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]
    login_attempts: int


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    user_id: Optional[str]
    username: Optional[str]
    role: Optional[str]
    message: str


@router.post("/users", response_model=UserResponse)
async def create_user(request: CreateUserRequest):
    """创建用户"""
    service = get_account_service()
    
    try:
        user = service.create_user(
            username=request.username,
            password=request.password,
            role=UserRole(request.role),
            email=request.email,
            phone=request.phone
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role.value,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
            login_attempts=user.login_attempts
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users")
async def get_users():
    """获取所有用户"""
    service = get_account_service()
    
    users = service.get_all_users()
    
    return {"users": users}


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """获取用户"""
    service = get_account_service()
    
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        login_attempts=user.login_attempts
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """登录"""
    service = get_account_service()
    
    user, result = service.authenticate(
        username=request.username,
        password=request.password,
        ip_address=request.ip_address,
        user_agent=request.user_agent
    )
    
    if result == LoginResult.SUCCESS:
        return LoginResponse(
            success=True,
            user_id=user.id,
            username=user.username,
            role=user.role.value,
            message="Login successful"
        )
    elif result == LoginResult.INVALID_PASSWORD:
        return LoginResponse(
            success=False,
            user_id=None,
            username=request.username,
            role=None,
            message="Invalid password"
        )
    elif result == LoginResult.USER_NOT_FOUND:
        return LoginResponse(
            success=False,
            user_id=None,
            username=request.username,
            role=None,
            message="User not found"
        )
    elif result == LoginResult.ACCOUNT_LOCKED:
        return LoginResponse(
            success=False,
            user_id=None,
            username=request.username,
            role=None,
            message="Account locked. Please try again later."
        )
    
    return LoginResponse(
        success=False,
        user_id=None,
        username=None,
        role=None,
        message="Login failed"
    )


@router.post("/password/change")
async def change_password(request: ChangePasswordRequest):
    """修改密码"""
    service = get_account_service()
    
    success = service.update_password(
        user_id=request.user_id,
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password. Check old password."
        )
    
    return {"message": "Password changed successfully"}


@router.post("/password/reset")
async def reset_password(request: ResetPasswordRequest):
    """重置密码（管理员）"""
    service = get_account_service()
    
    success = service.reset_password(
        user_id=request.user_id,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """删除用户"""
    service = get_account_service()
    
    success = service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.get("/logs")
async def get_login_logs(user_id: Optional[str] = None, limit: int = 50):
    """获取登录日志"""
    service = get_account_service()
    
    logs = service.get_login_logs(user_id, limit)
    
    return {
        "logs": [
            {
                "log_id": l.log_id,
                "username": l.username,
                "ip_address": l.ip_address,
                "user_agent": l.user_agent,
                "result": l.result.value,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ]
    }
