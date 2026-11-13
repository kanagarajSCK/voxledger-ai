from datetime import datetime, timezone, time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException
from app.models.customer import Customer
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.customer import CustomerSummary
from app.schemas.transaction import TransactionResponse


class LedgerService:
    @staticmethod
    async def get_customer_by_public_id(
        db: AsyncSession, public_id: str
    ) -> Optional[Customer]:
        """Fetch a customer by their public UUID."""
        stmt = select(Customer).where(Customer.public_id == public_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_customer_balance_stats(
        db: AsyncSession, customer_internal_id: int
    ) -> Dict[str, Decimal | int]:
        """
        Calculate exact financial balance for a customer.
        Outstanding Balance = Total CREDIT - Total PAYMENT
        """
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.CREDIT)
                            & (Transaction.status == TransactionStatus.COMPLETED),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_credit"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.PAYMENT)
                            & (Transaction.status == TransactionStatus.COMPLETED),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_payment"),
            func.count(
                case(
                    (Transaction.status == TransactionStatus.COMPLETED, Transaction.id),
                    else_=None,
                )
            ).label("transaction_count"),
        ).where(Transaction.customer_id == customer_internal_id)

        result = await db.execute(stmt)
        row = result.one()

        total_credit = Decimal(str(row.total_credit or "0.00"))
        total_payment = Decimal(str(row.total_payment or "0.00"))
        outstanding_balance = total_credit - total_payment
        transaction_count = int(row.transaction_count or 0)

        return {
            "total_credit": total_credit,
            "total_payment": total_payment,
            "outstanding_balance": outstanding_balance,
            "transaction_count": transaction_count,
        }

    @staticmethod
    async def get_customer_summary(
        db: AsyncSession, customer: Customer
    ) -> CustomerSummary:
        """Hydrate a Customer model into CustomerSummary with live balance."""
        stats = await LedgerService.get_customer_balance_stats(db, customer.id)
        return CustomerSummary(
            id=customer.public_id,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            outstanding_balance=stats["outstanding_balance"],
            total_credit=stats["total_credit"],
            total_payment=stats["total_payment"],
            transaction_count=stats["transaction_count"],
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )

    @staticmethod
    async def record_transaction(
        db: AsyncSession,
        customer_public_id: str,
        amount: Decimal,
        transaction_type: TransactionType,
        description: Optional[str] = None,
        voice_raw_text: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Transaction:
        """
        Record a credit or payment transaction with strict validations:
        - Amount must be > 0.
        - Customer must exist.
        - Payment cannot exceed customer's current outstanding balance.
        - Idempotency key deduplication.
        - Database transaction integrity.
        """
        if amount <= Decimal("0.00"):
            raise AppException(
                status_code=400,
                code="INVALID_AMOUNT",
                message="Transaction amount must be strictly greater than zero.",
            )

        # 1. Check idempotency key if provided
        if idempotency_key:
            stmt = (
                select(Transaction)
                .options(selectinload(Transaction.customer))
                .where(Transaction.idempotency_key == idempotency_key)
            )
            result = await db.execute(stmt)
            existing_tx = result.scalar_one_or_none()
            if existing_tx:
                return existing_tx

        # 2. Check customer existence
        customer = await LedgerService.get_customer_by_public_id(
            db, customer_public_id
        )
        if not customer:
            raise AppException(
                status_code=404,
                code="CUSTOMER_NOT_FOUND",
                message=f"Customer with ID '{customer_public_id}' does not exist.",
            )

        # 3. If PAYMENT, validate that payment does not exceed outstanding balance
        if transaction_type == TransactionType.PAYMENT:
            stats = await LedgerService.get_customer_balance_stats(db, customer.id)
            current_balance = stats["outstanding_balance"]

            if current_balance <= Decimal("0.00"):
                raise AppException(
                    status_code=400,
                    code="PAYMENT_EXCEEDS_BALANCE",
                    message="Customer has zero or negative outstanding balance. No payment is owed.",
                    details={"outstanding_balance": str(current_balance), "attempted_payment": str(amount)},
                )

            if amount > current_balance:
                raise AppException(
                    status_code=400,
                    code="PAYMENT_EXCEEDS_BALANCE",
                    message=f"Payment of ₹{amount:.2f} cannot exceed customer's outstanding balance of ₹{current_balance:.2f}.",
                    details={"outstanding_balance": str(current_balance), "attempted_payment": str(amount)},
                )

        # 4. Create transaction
        new_transaction = Transaction(
            customer_id=customer.id,
            amount=amount,
            type=transaction_type,
            status=TransactionStatus.COMPLETED,
            description=description,
            voice_raw_text=voice_raw_text,
            idempotency_key=idempotency_key,
        )

        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        # Reload with customer relationship
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.customer))
            .where(Transaction.id == new_transaction.id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def get_dashboard_summary(db: AsyncSession) -> Dict:
        """
        Calculate high-level dashboard metrics across actual database records.
        """
        # 1. Total customers
        total_customers = await db.scalar(select(func.count(Customer.id))) or 0

        # 2. Total outstanding credit across all customers
        total_credit_stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.CREDIT)
                            & (Transaction.status == TransactionStatus.COMPLETED),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_credit"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.PAYMENT)
                            & (Transaction.status == TransactionStatus.COMPLETED),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_payment"),
        )
        totals_result = await db.execute(total_credit_stmt)
        totals_row = totals_result.one()
        all_credit = Decimal(str(totals_row.total_credit or "0.00"))
        all_payment = Decimal(str(totals_row.total_payment or "0.00"))
        total_outstanding = max(Decimal("0.00"), all_credit - all_payment)

        # 3. Today's credit and today's payments (UTC start of day)
        now_utc = datetime.now(timezone.utc)
        start_of_today = datetime.combine(now_utc.date(), time.min).replace(tzinfo=timezone.utc)

        today_stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.CREDIT)
                            & (Transaction.status == TransactionStatus.COMPLETED)
                            & (Transaction.created_at >= start_of_today),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("today_credit"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == TransactionType.PAYMENT)
                            & (Transaction.status == TransactionStatus.COMPLETED)
                            & (Transaction.created_at >= start_of_today),
                            Transaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("today_payment"),
        )
        today_result = await db.execute(today_stmt)
        today_row = today_result.one()
        today_credit = Decimal(str(today_row.today_credit or "0.00"))
        today_payments = Decimal(str(today_row.today_payment or "0.00"))

        # 4. 10 Recent transactions
        recent_tx_stmt = (
            select(Transaction)
            .options(selectinload(Transaction.customer))
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
        recent_result = await db.execute(recent_tx_stmt)
        recent_transactions = [
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
            for tx in recent_result.scalars().all()
        ]

        return {
            "total_customers": total_customers,
            "total_outstanding_credit": total_outstanding,
            "today_credit": today_credit,
            "today_payments": today_payments,
            "recent_transactions": recent_transactions,
        }


ledger_service = LedgerService()
