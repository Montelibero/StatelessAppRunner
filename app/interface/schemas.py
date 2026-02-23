from typing import Optional

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    domain: Optional[str] = None
    key: str
    html: str
    compress: bool = False


class SaveAppRequest(BaseModel):
    key: str
    slug: str
    html: str
    owner_id: Optional[int] = None


class DeleteAppRequest(BaseModel):
    key: str
    owner_id: Optional[int] = None


class CreateUserRequest(BaseModel):
    key: str
    comment: Optional[str] = None
    admin_key: str
