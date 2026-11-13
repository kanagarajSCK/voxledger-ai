from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException
from app.db.session import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.ledger_service import ledger_service

router = APIRouter(tags=["Transactions"])


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new financial credit or payment transaction",
)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    tx = await ledger_service.record_transaction(
        db=db,
        customer_public_id=data.customer_id,
        amount=data.amount,
        transaction_type=data.type,
        description=data.description,
        voice_raw_text=data.voice_raw_text,
        idempotency_key=data.idempotency_key,
    )

    return TransactionResponse(
        id=tx.public_id,
        customer_id=tx.customer.public_id,
        customer_name=tx.customer.name,
        amount=tx.amount,
        type=tx.type,
        status=tx.status,
        description=tx.description,
        voice_raw_text=tx.voice_raw_text,
        idempotency_key=tx.idempotency_key,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="List transactions across all customers",
)
async def list_transactions(
    type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    query = select(Transaction).options(selectinload(Transaction.customer))
    count_query = select(func.count(Transaction.id))

    if type:
        query = query.where(Transaction.type == type)
        count_query = count_query.where(Transaction.type == type)

    total = await db.scalar(count_query) or 0
    query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()

    items = [
        TransactionResponse(
            id=tx.public_id,
            customer_id=tx.customer.public_id,
            customer_name=tx.customer.name,
            amount=tx.amount,
            type=tx.type,
            status=tx.status,
            description=tx.description,
            voice_raw_text=tx.voice_raw_text,
            idempotency_key=tx.idempotency_key,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
        )
        for tx in transactions
    ]

    return TransactionListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    summary="Retrieve a specific transaction by ID",
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.customer))
        .where(Transaction.public_id == transaction_id)
    )
    result = await db.execute(stmt)
    tx = result.scalar_one_or_none()

    if not tx:
        raise AppException(
            status_code=404,
            code="TRANSACTION_NOT_FOUND",
            message=f"Transaction with ID '{transaction_id}' was not found.",
        )

    return TransactionResponse(
        id=tx.public_id,
        customer_id=tx.customer.public_id,
        customer_name=tx.customer.name,
        amount=tx.amount,
        type=tx.type,
        status=tx.status,
        description=tx.description,
        voice_raw_text=tx.voice_raw_text,
        idempotency_key=tx.idempotency_key,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


@router.get(
    "/customers/{customer_id}/transactions",
    response_model=TransactionListResponse,
    summary="List all transaction history for a specific customer",
)
async def get_customer_transactions(
    customer_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    customer = await ledger_service.get_customer_by_public_id(db, customer_id)
    if not customer:
        raise AppException(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=f"Customer with ID '{customer_id}' was not found.",
        )

    query = (
        select(Transaction)
        .options(selectinload(Transaction.customer))
        .where(Transaction.customer_id == customer.id)
    )
    count_query = select(func.count(Transaction.id)).where(
        Transaction.customer_id == customer.id
    )

    total = await db.scalar(count_query) or 0
    query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()

    items = [
        TransactionResponse(
            id=tx.public_id,
            customer_id=customer.public_id,
            customer_name=customer.name,
            amount=tx.amount,
            type=tx.type,
            status=tx.status,
            description=tx.description,
            voice_raw_text=tx.voice_raw_text,
            idempotency_key=tx.idempotency_key,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
        )
        for tx in transactions
    ]

    return TransactionListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )
