import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.customer import Customer
from app.models.transaction import Transaction, TransactionType


@pytest.mark.asyncio
async def test_create_customer_and_transactions(db_session: AsyncSession):
    # 1. Create a customer
    customer = Customer(
        name="Sunil Kirana Stores",
        phone="+919876543210",
        address="Market Yard, Shop #12",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    assert customer.id is not None
    assert customer.public_id is not None
    assert len(customer.public_id) == 36
    assert customer.name == "Sunil Kirana Stores"

    # 2. Add a CREDIT transaction (Goods given on udhar)
    t1 = Transaction(
        customer_id=customer.id,
        amount=Decimal("1250.50"),
        type=TransactionType.CREDIT,
        description="Rice 10kg, Cooking Oil 2L",
        voice_raw_text="Sunil ko barah sau pachas ka samaan diya",
    )
    # 3. Add a PAYMENT transaction (Partial payment received)
    t2 = Transaction(
        customer_id=customer.id,
        amount=Decimal("500.00"),
        type=TransactionType.PAYMENT,
        description="Cash payment via UPI",
        voice_raw_text="Sunil ne paanch sau rupaye diye",
    )
    db_session.add_all([t1, t2])
    await db_session.commit()

    # 4. Refresh customer with transactions loaded
    stmt = (
        select(Customer)
        .where(Customer.id == customer.id)
        .options(selectinload(Customer.transactions))
        .execution_options(populate_existing=True)
    )
    result = await db_session.execute(stmt)
    fetched_customer = result.scalar_one()

    assert len(fetched_customer.transactions) == 2
    amounts = [t.amount for t in fetched_customer.transactions]
    assert Decimal("1250.50") in amounts
    assert Decimal("500.00") in amounts

    # 5. Verify transaction navigates back to customer
    assert fetched_customer.transactions[0].customer.name == "Sunil Kirana Stores"


@pytest.mark.asyncio
async def test_customer_cascade_delete(db_session: AsyncSession):
    customer = Customer(name="Test Cascade", phone="+919999999999")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    t = Transaction(
        customer_id=customer.id,
        amount=Decimal("100.00"),
        type=TransactionType.CREDIT,
    )
    db_session.add(t)
    await db_session.commit()
    t_id = t.id

    # Delete customer
    await db_session.delete(customer)
    await db_session.commit()

    # Expire/clear session cache and verify transaction was deleted
    db_session.expire_all()
    result = await db_session.execute(select(Transaction).where(Transaction.id == t_id))
    assert result.scalar_one_or_none() is None
