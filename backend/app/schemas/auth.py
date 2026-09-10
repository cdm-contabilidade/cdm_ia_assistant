from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=200)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = ' '.join(value.split())
        if not normalized:
            raise ValueError('nome obrigatório')
        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AdminUserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        normalized = ' '.join(value.split()) if value is not None else None
        if value is not None and not normalized:
            raise ValueError('nome obrigatório')
        return normalized
    password: str | None = Field(default=None, min_length=8, max_length=200)
    is_active: bool | None = None
    is_blacklisted: bool | None = None

    @model_validator(mode='after')
    def require_change(self):
        if all(value is None for value in (self.name, self.password, self.is_active, self.is_blacklisted)):
            raise ValueError('informe ao menos uma alteração')
        return self
