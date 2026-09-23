from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProviderName = Literal['gemini', 'openai']


class ProviderKeyUpdate(BaseModel):
    api_key: str = Field(validation_alias='apiKey', min_length=1, max_length=4096)

    model_config = {'populate_by_name': True}


class ProviderKeyStatusPublic(BaseModel):
    provider: ProviderName
    configured: bool
    source: Literal['database', 'environment', 'none']
    last4: str | None = None
    masked_last4: str | None = Field(default=None, serialization_alias='maskedLast4')
    updated_at: datetime | None = Field(default=None, serialization_alias='updatedAt')
    disabled: bool = False

    model_config = {'populate_by_name': True}
