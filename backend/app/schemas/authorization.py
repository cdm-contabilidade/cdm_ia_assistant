from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @model_validator(mode='after')
    def normalize_name(self):
        self.name = ' '.join(self.name.split())
        if not self.name:
            raise ValueError('nome obrigatório')
        return self


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode='after')
    def normalize_name(self):
        if self.name is not None:
            self.name = ' '.join(self.name.split())
            if not self.name:
                raise ValueError('nome obrigatório')
        if self.name is None:
            raise ValueError('informe ao menos uma alteração')
        return self


class GroupMembersReplace(BaseModel):
    user_ids: list[UUID] = Field(
        default_factory=list,
        validation_alias=AliasChoices('userIds', 'user_ids'),
        serialization_alias='userIds',
    )

    model_config = ConfigDict(populate_by_name=True)


class GroupGrantsReplace(BaseModel):
    knowledge_base_ids: list[UUID] = Field(
        default_factory=list,
        validation_alias=AliasChoices('knowledgeBaseIds', 'knowledge_base_ids'),
        serialization_alias='knowledgeBaseIds',
    )
    web_search: bool = Field(
        default=False,
        validation_alias=AliasChoices('webSearch', 'web_search'),
        serialization_alias='webSearch',
    )

    model_config = ConfigDict(populate_by_name=True)


class PermissionOverride(BaseModel):
    capability: Literal['knowledge_base', 'web_search']
    knowledge_base_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices('knowledgeBaseId', 'knowledge_base_id'),
        serialization_alias='knowledgeBaseId',
    )
    allowed: bool

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_target(self):
        if self.capability == 'knowledge_base' and self.knowledge_base_id is None:
            raise ValueError('knowledge_base requer knowledgeBaseId')
        if self.capability == 'web_search' and self.knowledge_base_id is not None:
            raise ValueError('web_search não aceita knowledgeBaseId')
        return self


class PermissionOverridesReplace(BaseModel):
    overrides: list[PermissionOverride] = Field(default_factory=list)

    @model_validator(mode='after')
    def reject_duplicate_targets(self):
        targets = [(item.capability, item.knowledge_base_id) for item in self.overrides]
        if len(targets) != len(set(targets)):
            raise ValueError('não pode haver mais de um override para o mesmo recurso')
        return self


class GroupPublic(BaseModel):
    id: UUID
    name: str
    user_ids: list[UUID] = Field(default_factory=list, serialization_alias='userIds')
    knowledge_base_ids: list[UUID] = Field(default_factory=list, serialization_alias='knowledgeBaseIds')
    web_search: bool = Field(default=False, serialization_alias='webSearch')
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PermissionOverridePublic(PermissionOverride):
    id: UUID
    user_id: UUID = Field(serialization_alias='userId')
