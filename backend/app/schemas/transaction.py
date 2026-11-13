from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.transaction import TransactionType, TransactionStatus


class TransactionCreate(BaseModel):
    customer_id: str = Field(..., description="Public UUID of customer", example="550e8400-e29b-41d4-a716-446655440000")
    amount: Decimal = Field(..., gt=0, decimal_places=2, example=150.00)
    type: TransactionType = Field(..., example=TransactionType.CREDIT)
    description: Optional[str] = Field(None, max_length=255, example="2kg Sugar, 1L Mustard Oil")
    voice_raw_text: Optional[str] = Field(None, example="Ramesh ko dedh sau rupaye ka rashan diya")
    idempotency_key: Optional[str] = Field(None, max_length=64, example="req_abc123_uuid")


class TransactionResponse(BaseModel):
    id: str = Field(..., description="Public UUID of transaction")
    customer_id: str = Field(..., description="Public UUID of customer")
    customer_name: Optional[str] = None
    amount: Decimal = Field(..., decimal_places=2)
    type: TransactionType
    status: TransactionStatus
    description: Optional[str] = None
    voice_raw_text: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    total: int
    items: List[TransactionResponse]
    limit: int
    offset: int
