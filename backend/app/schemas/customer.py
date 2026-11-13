from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Ramesh Kumar")
    phone: Optional[str] = Field(None, max_length=20, example="+919876543210")
    address: Optional[str] = Field(None, max_length=255, example="Shop 4, Gandhi Market")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)


class CustomerSummary(BaseModel):
    id: str = Field(..., description="Public UUID of customer")
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    outstanding_balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_credit: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_payment: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    transaction_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    total: int
    items: List[CustomerSummary]
    limit: int
    offset: int


class CustomerDetailResponse(CustomerSummary):
    pass
