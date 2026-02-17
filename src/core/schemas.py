from beanie import PydanticObjectId
from fastapi_users import schemas


class UserRead(schemas.BaseUser[PydanticObjectId]):
    full_name: str | None = None
    role: str
    permissions: list[str]


class UserCreate(schemas.BaseUserCreate):
    full_name: str | None = None
    role: str = "user"
    permissions: list[str] = []


class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = None
    role: str | None = None
    permissions: list[str] | None = None
