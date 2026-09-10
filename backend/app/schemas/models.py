from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    name: str
    role: Literal['admin', 'collaborator']
    is_active: bool
    is_blacklisted: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserPublic


class ChatSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    content: str
    created_at: datetime
    has_image: bool
    image_metadata: dict | None = None


class HistoryMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=10000)


class SourceCitation(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    uri: str | None = None
    text: str | None = None
    page_number: int | None = Field(default=None, alias='pageNumber')

    model_config = ConfigDict(populate_by_name=True)


class ChatQueryRequest(BaseModel):
    session_id: UUID = Field(alias='sessionId')
    chat_input: str = Field(alias='chatInput', min_length=1, max_length=10000)
    image: str | None = None
    chat_id: UUID | None = Field(default=None, alias='chatId')
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(populate_by_name=True)


class ChatQueryResponse(BaseModel):
    session_id: UUID = Field(alias='sessionId')
    chat_id: UUID | None = Field(alias='chatId')
    answer: str
    messages: list[MessagePublic]
    sources: list[SourceCitation] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)




class ChatCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
