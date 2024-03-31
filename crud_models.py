from pydantic import ConfigDict, BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    id: int
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None