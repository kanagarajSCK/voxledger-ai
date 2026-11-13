from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    amount: Decimal = Field(..., gt=0, decimal_places=2, example=150.00)
    type: TransactionType = Field(..., example=TransactionType.CREDIT)
    description: Optional[str] = Field(None, max_length=255, example="2kg Sugar, 1L Milk")
    voice_raw_text: Optional[str] = Field(None, example="Ramesh ko dedh sau rupaye ka rashan diya")


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    public_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
