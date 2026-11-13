from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Ramesh Kumar")
    phone: str = Field(..., min_length=10, max_length=15, example="+919876543210")
    address: Optional[str] = Field(None, max_length=255, example="Shop 4, Gandhi Market")


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    public_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
