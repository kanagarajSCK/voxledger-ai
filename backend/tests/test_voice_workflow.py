from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.services.voice_workflow_service import VoiceWorkflowService, voice_workflow
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
async def test_voice_workflow_duplicate_confirmation_is_idempotent(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_duplicate_confirm"
    res1 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 150 rupees udhaar podu.",
        language="en-IN",
    )
    assert res1["type"] == "action_proposed"

    res2 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert res2["type"] == "action_executed"
    assert res2["transaction"]["amount"] == "150.00"

    res3 = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert res3["type"] == "action_executed"
    assert res3["transaction"]["id"] == res2["transaction"]["id"]

    txs = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs) == 1
    assert txs[0].amount == Decimal("150.00")


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


def test_voice_workflow_session_cleanup_removes_expired_entries():
    workflow = VoiceWorkflowService(session_ttl_seconds=30)
    expired_session_id = "expired-session"
    expired_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).timestamp()
    workflow._sessions[expired_session_id] = {"session_id": expired_session_id, "expires_at": expired_time}
    workflow._sessions["keep-me"] = {"session_id": "keep-me", "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()}

    workflow.get_or_create_session("new-active-session")

    assert expired_session_id not in workflow._sessions
    assert "keep-me" in workflow._sessions
    assert "new-active-session" in workflow._sessions


@pytest.mark.asyncio
async def test_voice_workflow_corrected_credit_commits_350_only(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    workflow = VoiceWorkflowService()
    session_id = "test_session_corrected_commit"

    proposed = await workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh 500 rupees credit",
        language="en-IN",
    )
    assert proposed["type"] == "action_proposed"
    assert proposed["action"]["amount"] == "500"

    corrected = await workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 500 illa, 350.",
        language="en-IN",
    )
    assert corrected["type"] == "action_proposed"
    assert corrected["action"]["amount"] == "350"
    assert corrected["action"]["previous_action_id"] == proposed["action"]["action_id"]
    assert corrected["action"]["action_id"] != proposed["action"]["action_id"]

    confirmed = await workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert confirmed["type"] == "action_executed"
    assert confirmed["transaction"]["amount"] == "350.00"

    stats = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats["outstanding_balance"] == Decimal("350.00")

    txs = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs) == 1
    assert txs[0].amount == Decimal("350.00")
    assert all(tx.amount != Decimal("500.00") for tx in txs)


@pytest.mark.asyncio
async def test_voice_workflow_expired_session_rejects_stale_confirmation(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_expired"
    workflow = VoiceWorkflowService(session_ttl_seconds=60)
    session = workflow.get_or_create_session(session_id)
    session["pending_action"] = {
        "action_id": "act_expired_1",
        "customer_id": ramesh.id,
        "customer_public_id": ramesh.public_id,
        "customer_name": ramesh.name,
        "type": "CREDIT",
        "amount": "500",
        "current_balance": "0.00",
        "projected_balance": "500.00",
        "description": "Expired voice proposal",
        "raw_text": "Ramesh 500 credit",
        "idempotency_key": "voice_act_expired_1",
    }
    session["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()

    result = await workflow._execute_pending_action(db_session, session)
    assert result["type"] == "expired_session"

    stats = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats["outstanding_balance"] == Decimal("0.00")
    txs = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs) == 0


@pytest.mark.asyncio
async def test_voice_workflow_new_session_isolated_from_old_idempotency_state(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    workflow = VoiceWorkflowService(session_ttl_seconds=60)

    old_session = workflow.get_or_create_session("old-session-isolated")
    old_session["pending_action"] = {
        "action_id": "act_old_1",
        "customer_id": ramesh.id,
        "customer_public_id": ramesh.public_id,
        "customer_name": ramesh.name,
        "type": "CREDIT",
        "amount": "200",
        "current_balance": "0.00",
        "projected_balance": "200.00",
        "description": "stale action",
        "raw_text": "Ramesh 200 credit",
        "idempotency_key": "voice_act_old_1",
    }
    old_session["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()

    stale_result = await workflow._execute_pending_action(db_session, old_session)
    assert stale_result["type"] == "expired_session"

    new_session = workflow.get_or_create_session("new-session-isolated")
    empty_result = await workflow._execute_pending_action(db_session, new_session)
    assert empty_result["type"] == "no_pending_action"

    stats_before = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats_before["outstanding_balance"] == Decimal("0.00")

    legit = await workflow.handle_transcript(
        db=db_session,
        session_id="new-session-isolated",
        transcript="Ramesh 75 rupees credit",
        language="en-IN",
    )
    assert legit["type"] == "action_proposed"

    confirmed = await workflow.handle_transcript(
        db=db_session,
        session_id="new-session-isolated",
        transcript="Yes",
        language="en-IN",
    )
    assert confirmed["type"] == "action_executed"
    assert confirmed["transaction"]["amount"] == "75.00"

    stats_after = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats_after["outstanding_balance"] == Decimal("75.00")

    txs = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs) == 1
    assert txs[0].amount == Decimal("75.00")


@pytest.mark.asyncio
async def test_voice_workflow_cancellation_blocks_commit_and_replay(db_session: AsyncSession):
    ramesh = Customer(name="Ramesh", phone="+919876543210")
    db_session.add(ramesh)
    await db_session.commit()
    await db_session.refresh(ramesh)

    session_id = "test_session_cancelled"

    proposed = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Ramesh-ku 500 rupees udhar.",
        language="en-IN",
    )
    assert proposed["type"] == "action_proposed"

    cancelled = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Cancel",
        language="en-IN",
    )
    assert cancelled["type"] == "action_cancelled"

    stats = await ledger_service.get_customer_balance_stats(db_session, ramesh.id)
    assert stats["outstanding_balance"] == Decimal("0.00")

    txs = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs) == 0

    replay = await voice_workflow.handle_transcript(
        db=db_session,
        session_id=session_id,
        transcript="Yes",
        language="en-IN",
    )
    assert replay["type"] == "no_pending_action"

    txs_after_replay = (await db_session.execute(select(Transaction))).scalars().all()
    assert len(txs_after_replay) == 0
