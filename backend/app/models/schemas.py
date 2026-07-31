from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

# Auth Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=2, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Room Schemas
class CreateRoomRequest(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = "python"
    duration_hours: Optional[int] = 24
    max_participants: Optional[int] = 10
    is_public: Optional[bool] = False
    initial_code: Optional[str] = None

class RoomResponse(BaseModel):
    id: str
    code: str
    name: str
    language: str
    owner_id: Optional[str]
    created_at: str
    expires_at: str
    max_participants: int
    is_public: bool
    initial_code: str

# Code Execution Schemas
class ExecuteCodeRequest(BaseModel):
    code: str
    language: str = "python"
    stdin: Optional[str] = None

class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    blocked: bool = False
    metadata: Dict[str, Any] = {}

# Cursor Pagination Response
class PaginatedExecutionLogs(BaseModel):
    items: List[Dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool = False
