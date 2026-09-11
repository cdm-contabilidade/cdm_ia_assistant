from datetime import datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


_FILE_SEARCH_STORE_PATTERN = re.compile(r'^fileSearchStores/[^/\s]+$')


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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    role: str
    content: str
    created_at: datetime
    has_image: bool
    image_metadata: dict | None = None
    metadata: dict | None = Field(default=None, validation_alias='provider_metadata', serialization_alias='metadata')


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
    images: list[str] = Field(default_factory=list, max_length=4)
    chat_id: UUID | None = Field(default=None, alias='chatId')
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)
    model_id: UUID | None = Field(default=None, alias='modelId')
    knowledge_base_id: UUID | None = Field(default=None, alias='knowledgeBaseId')

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def reject_mixed_image_fields(self):
        if self.image is not None and self.images:
            raise ValueError('image e images não podem ser enviados juntos')
        return self


class ChatQueryResponse(BaseModel):
    session_id: UUID = Field(alias='sessionId')
    chat_id: UUID | None = Field(alias='chatId')
    title: str | None = None
    answer: str
    messages: list[MessagePublic]
    sources: list[SourceCitation] = Field(default_factory=list)
    model_id: UUID | None = Field(default=None, alias='modelId')
    knowledge_base_id: UUID | None = Field(default=None, alias='knowledgeBaseId')
    model: dict | None = None
    knowledge_base: dict | None = Field(default=None, alias='knowledgeBase')

    model_config = ConfigDict(populate_by_name=True)




class ChatCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class AIModelCreate(BaseModel):
    provider: Literal['gemini', 'openai']
    display_name: str = Field(
        validation_alias=AliasChoices('displayName', 'display_name', 'name'),
        serialization_alias='displayName', min_length=1, max_length=120,
    )
    model_id: str = Field(validation_alias=AliasChoices('modelId', 'model_id'), serialization_alias='modelId', min_length=1, max_length=255)
    active: bool = Field(default=True, validation_alias=AliasChoices('active', 'isActive', 'is_active'))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('display_name', 'model_id')
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = ' '.join(value.split()) if value != value.strip() or '  ' in value else value
        if not value:
            raise ValueError('valor obrigatório')
        return value

    @field_validator('model_id')
    @classmethod
    def reject_openai_secret(cls, value: str) -> str:
        if 'sk-' in value.lower():
            raise ValueError('model_id não pode conter uma chave OpenAI')
        return value


class AIModelUpdate(BaseModel):
    provider: Literal['gemini', 'openai'] | None = None
    display_name: str | None = Field(
        default=None, validation_alias=AliasChoices('displayName', 'display_name', 'name'),
        serialization_alias='displayName', min_length=1, max_length=120,
    )
    model_id: str | None = Field(default=None, validation_alias=AliasChoices('modelId', 'model_id'), serialization_alias='modelId', min_length=1, max_length=255)
    active: bool | None = Field(default=None, validation_alias=AliasChoices('active', 'isActive', 'is_active'))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('display_name', 'model_id')
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return ' '.join(value.split()) if value is not None else None

    @field_validator('model_id')
    @classmethod
    def reject_openai_secret(cls, value: str | None) -> str | None:
        if value is not None and 'sk-' in value.lower():
            raise ValueError('model_id não pode conter uma chave OpenAI')
        return value

    @model_validator(mode='after')
    def require_change(self):
        if all(value is None for value in (self.provider, self.display_name, self.model_id, self.active)):
            raise ValueError('informe ao menos uma alteração')
        return self


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: Literal['gemini'] = 'gemini'
    file_search_store_id: str = Field(
        validation_alias=AliasChoices('fileSearchStoreId', 'file_search_store_id', 'store_id', 'storeId'),
        serialization_alias='fileSearchStoreId', min_length=1, max_length=255,
    )
    active: bool = Field(default=True, validation_alias=AliasChoices('active', 'isActive', 'is_active'))
    featured: bool = False

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('name', 'file_search_store_id')
    @classmethod
    def normalize_kb_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('valor obrigatório')
        return value

    @field_validator('file_search_store_id')
    @classmethod
    def validate_store_id(cls, value: str) -> str:
        if not _FILE_SEARCH_STORE_PATTERN.fullmatch(value):
            raise ValueError('file_search_store_id deve usar o formato fileSearchStores/<id>')
        return value

    @model_validator(mode='after')
    def normalize_inactive_featured(self):
        if not self.active:
            self.featured = False
        return self


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider: Literal['gemini'] | None = None
    file_search_store_id: str | None = Field(
        default=None, validation_alias=AliasChoices('fileSearchStoreId', 'file_search_store_id', 'store_id', 'storeId'),
        serialization_alias='fileSearchStoreId', min_length=1, max_length=255,
    )
    active: bool | None = Field(default=None, validation_alias=AliasChoices('active', 'isActive', 'is_active'))
    featured: bool | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('name', 'file_search_store_id')
    @classmethod
    def normalize_optional_kb_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator('file_search_store_id')
    @classmethod
    def validate_store_id(cls, value: str | None) -> str | None:
        if value is not None and not _FILE_SEARCH_STORE_PATTERN.fullmatch(value):
            raise ValueError('file_search_store_id deve usar o formato fileSearchStores/<id>')
        return value

    @model_validator(mode='after')
    def normalize_inactive_featured(self):
        if self.active is False:
            self.featured = False
        return self

    @model_validator(mode='after')
    def require_change(self):
        if all(value is None for value in (self.name, self.provider, self.file_search_store_id, self.active, self.featured)):
            raise ValueError('informe ao menos uma alteração')
        return self


class AIModelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    provider: Literal['gemini', 'openai']
    display_name: str = Field(serialization_alias='displayName')
    model_id: str = Field(serialization_alias='modelId')
    active: bool
    # Legacy read aliases are retained for the existing backend consumer.
    name: str = Field(validation_alias='display_name', serialization_alias='name')
    is_active: bool = Field(validation_alias='active', serialization_alias='is_active')
    display_name_legacy: str = Field(validation_alias='display_name', serialization_alias='display_name')
    model_id_legacy: str = Field(validation_alias='model_id', serialization_alias='model_id')
    created_at: datetime
    updated_at: datetime


class AIModelCatalogPublic(BaseModel):
    """Public catalog view without administrative timestamps or secrets."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    # ``name`` is the public label and keeps the existing catalog consumer
    # compatible while avoiding provider credentials or internal metadata.
    name: str = Field(validation_alias='display_name', serialization_alias='name')
    provider: Literal['gemini', 'openai']
    model_id: str = Field(serialization_alias='modelId')
    active: bool


class KnowledgeBasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    name: str
    provider: Literal['gemini']
    file_search_store_id: str = Field(serialization_alias='fileSearchStoreId')
    active: bool
    featured: bool
    store_id: str = Field(validation_alias='file_search_store_id', serialization_alias='store_id')
    is_active: bool = Field(validation_alias='active', serialization_alias='is_active')
    file_search_store_id_legacy: str = Field(validation_alias='file_search_store_id', serialization_alias='file_search_store_id')
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseCatalogPublic(BaseModel):
    """Safe collaborator-facing view; provider resource IDs stay admin-only."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    name: str
    provider: Literal['gemini']
    active: bool
    featured: bool
