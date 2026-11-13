from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field
from app.schemas.transaction import TransactionResponse


class DashboardSummaryResponse(BaseModel):
    total_customers: int = Field(..., example=42)
    total_outstanding_credit: Decimal = Field(..., decimal_places=2, example=12450.50)
    today_credit: Decimal = Field(..., decimal_places=2, example=1500.00)
    today_payments: Decimal = Field(..., decimal_places=2, example=850.00)
    recent_transactions: List[TransactionResponse] = Field(default_factory=list)
