from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.services.voice_workflow_service import voice_workflow
from app.services.ledger_service import ledger_service


@pytest.mark.asyncio
async def test_voice_workflow_full_lifecycle(db_session: AsyncSession):
    # 1. Create a customer "Ramesh"
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_1"

    # 2. Step 1: Speak "Ramesh-ku 340 rupees udhaar podu." -> Expect action_proposed
    res1 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 340 rupees udhaar podu.",
        language="en-IN",
    )
    assert res1["type"] == "action_proposed"
    assert res1["action"]["customer_name"] == "Ramesh"
    assert res1["action"]["amount"] == "340"
    assert res1["action"]["type"] == "CREDIT"
    assert res1["action"]["current_balance"] == "0.00"
    assert res1["action"]["projected_balance"] == "340.00"

    # Database balance should STILL BE 0.00 before confirmation!
    stats_before = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats_before["outstanding_balance"] == Decimal("0.00")

    # 3. Step 2: Speak "Yes" to confirm -> Expect action_executed
    res2 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert res2["type"] == "action_executed"
    assert res2["transaction"]["amount"] == "340.00"
    assert res2["transaction"]["new_balance"] == "340.00"

    # Database balance MUST now be exactly 340.00!
    stats_after_credit = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats_after_credit["outstanding_balance"] == Decimal("340.00")

    # 4. Step 3: Speak "Ramesh paid 200 rupees." -> Expect action_proposed
    res3 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh paid 200 rupees.",
        language="en-IN",
    )
    assert res3["type"] == "action_proposed"
    assert res3["action"]["type"] == "PAYMENT"
    assert res3["action"]["amount"] == "200"
    assert res3["action"]["projected_balance"] == "140.00"

    # 5. Step 4: Speak "Yes" to confirm payment
    res4 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert res4["type"] == "action_executed"
    assert res4["transaction"]["new_balance"] == "140.00"

    # Database balance MUST now be exactly 140.00!
    stats_after_pay = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats_after_pay["outstanding_balance"] == Decimal("140.00")

    # 6. Step 5: Speak "How much does Ramesh owe?" -> Expect balance_report
    res5 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="How much does Ramesh owe?",
        language="en-IN",
    )
    assert res5["type"] == "balance_report"
    assert res5["outstanding_balance"] == "140.00"
    assert "140" in res5["spoken_response"]


@pytest.mark.asyncio
async def test_voice_workflow_overpayment_rejection(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_2"

    # Attempt to record payment when balance is 0
    res = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh paid 100 rupees.",
        language="en-IN",
    )
    assert res["type"] == "payment_rejected"


@pytest.mark.asyncio
async def test_voice_workflow_correction(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_3"

    # Propose 500
    await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 500 rupees udhar.",
        language="en-IN",
    )

    # Correct: "Ramesh-ku 500 illa, 350."
    res_correct = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 500 illa, 350.",
        language="en-IN",
    )
    assert res_correct["type"] == "action_proposed"
    assert res_correct["action"]["amount"] == "350"
    assert res_correct["action"]["projected_balance"] == "350.00"

    # Cancel action
    res_cancel = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Cancel",
        language="en-IN",
    )
    assert res_cancel["type"] == "action_cancelled"

    # DB balance should remain 0
    stats = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats["outstanding_balance"] == Decimal("0.00")
