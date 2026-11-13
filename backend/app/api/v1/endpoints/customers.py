from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException
from app.db.session import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerListResponse,
    CustomerSummary,
    CustomerUpdate,
)
from app.services.ledger_service import ledger_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="List and search customers with calculated ledger balances",
)
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name or phone number"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> CustomerListResponse:
    # Build filter query
    query = select(Customer)
    count_query = select(func.count(Customer.id))

    if search:
        search_term = f"%{search.strip()}%"
        filter_cond = or_(
            Customer.name.ilike(search_term),
            Customer.phone.ilike(search_term),
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    # Get total count
    total = await db.scalar(count_query) or 0

    # Apply pagination and sorting
    query = query.order_by(Customer.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()

    # Hydrate customer summaries with ledger balances
    items = [
        await ledger_service.get_customer_summary(db, customer)
        for customer in customers
    ]

    return CustomerListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=CustomerSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer profile",
)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
) -> CustomerSummary:
    clean_name = data.name.strip()
    if not clean_name:
        raise AppException(
            status_code=400,
            code="INVALID_CUSTOMER_NAME",
            message="Customer name cannot be empty or whitespace only.",
        )

    # If phone is provided, check for duplicate phone number
    if data.phone and data.phone.strip():
        clean_phone = data.phone.strip()
        existing_phone = await db.scalar(
            select(Customer).where(Customer.phone == clean_phone)
        )
        if existing_phone:
            raise AppException(
                status_code=409,
                code="DUPLICATE_PHONE_NUMBER",
                message=f"A customer with phone number '{clean_phone}' already exists ({existing_phone.name}).",
            )
    else:
        clean_phone = None

    customer = Customer(
        name=clean_name,
        phone=clean_phone,
        address=data.address.strip() if data.address else None,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return await ledger_service.get_customer_summary(db, customer)


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    summary="Retrieve customer details with ledger balance",
)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
) -> CustomerDetailResponse:
    customer = await ledger_service.get_customer_by_public_id(db, customer_id)
    if not customer:
        raise AppException(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=f"Customer with ID '{customer_id}' was not found.",
        )

    return await ledger_service.get_customer_summary(db, customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerSummary,
    summary="Update customer profile information",
)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
) -> CustomerSummary:
    customer = await ledger_service.get_customer_by_public_id(db, customer_id)
    if not customer:
        raise AppException(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=f"Customer with ID '{customer_id}' was not found.",
        )

    if data.name is not None:
        clean_name = data.name.strip()
        if not clean_name:
            raise AppException(
                status_code=400,
                code="INVALID_CUSTOMER_NAME",
                message="Customer name cannot be empty.",
            )
        customer.name = clean_name

    if data.phone is not None:
        clean_phone = data.phone.strip() if data.phone.strip() else None
        if clean_phone and clean_phone != customer.phone:
            # Check for conflict with another customer
            existing_phone = await db.scalar(
                select(Customer).where(
                    Customer.phone == clean_phone, Customer.id != customer.id
                )
            )
            if existing_phone:
                raise AppException(
                    status_code=409,
                    code="DUPLICATE_PHONE_NUMBER",
                    message=f"Phone number '{clean_phone}' is already registered to customer '{existing_phone.name}'.",
                )
        customer.phone = clean_phone

    if data.address is not None:
        customer.address = data.address.strip() if data.address.strip() else None

    await db.commit()
    await db.refresh(customer)

    return await ledger_service.get_customer_summary(db, customer)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a customer (only if zero financial transactions exist)",
)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    customer = await ledger_service.get_customer_by_public_id(db, customer_id)
    if not customer:
        raise AppException(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=f"Customer with ID '{customer_id}' was not found.",
        )

    # Check if customer has any financial transactions
    tx_count = await db.scalar(
        select(func.count(Transaction.id)).where(Transaction.customer_id == customer.id)
    ) or 0

    if tx_count > 0:
        raise AppException(
            status_code=400,
            code="CUSTOMER_HAS_TRANSACTIONS",
            message=f"Cannot delete customer '{customer.name}' because {tx_count} financial transaction record(s) exist. Financial history must be preserved.",
            details={"transaction_count": tx_count},
        )

    await db.delete(customer)
    await db.commit()
    return None
