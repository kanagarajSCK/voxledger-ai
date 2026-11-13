import asyncio
from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_retrieve_customer(async_client: AsyncClient):
    # 1. Create Customer
    payload = {
        "name": "Ramesh Kumar",
        "phone": "+919876500001",
        "address": "Kirana Shop #1, Main Market",
    }
    res = await async_client.post("/api/v1/customers", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Ramesh Kumar"
    assert data["phone"] == "+919876500001"
    assert data["outstanding_balance"] == "0.00"
    assert data["total_credit"] == "0.00"
    assert data["total_payment"] == "0.00"
    assert data["transaction_count"] == 0
    customer_id = data["id"]

    # 2. Retrieve Customer
    get_res = await async_client.get(f"/api/v1/customers/{customer_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == customer_id
    assert get_data["name"] == "Ramesh Kumar"


@pytest.mark.asyncio
async def test_search_customers(async_client: AsyncClient):
    # Seed customers
    await async_client.post(
        "/api/v1/customers",
        json={"name": "Suresh Patel", "phone": "+919111111111"},
    )
    await async_client.post(
        "/api/v1/customers",
        json={"name": "Mahesh Verma", "phone": "+919222222222"},
    )

    # Search by name
    res1 = await async_client.get("/api/v1/customers?search=Suresh")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["items"]) == 1
    assert data1["items"][0]["name"] == "Suresh Patel"

    # Search by phone
    res2 = await async_client.get("/api/v1/customers?search=922222")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["name"] == "Mahesh Verma"


@pytest.mark.asyncio
async def test_credit_and_payment_balance_calculation(async_client: AsyncClient):
    """
    Ramesh Example from Specification:
    Credit: ₹500
    Payment: ₹200
    Credit: ₹300
    Expected outstanding balance: ₹600.00
    """
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Ramesh Gupta", "phone": "+919333333333"},
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    # 1. Credit ₹500
    tx1 = await async_client.post(
        "/api/v1/transactions",
        json={
            "customer_id": cust_id,
            "amount": 500.00,
            "type": "CREDIT",
            "description": "5kg Atta, 2kg Sugar",
        },
    )
    assert tx1.status_code == 201

    # Check balance after Credit 1
    c1 = await async_client.get(f"/api/v1/customers/{cust_id}")
    assert c1.json()["outstanding_balance"] == "500.00"
    assert c1.json()["total_credit"] == "500.00"
    assert c1.json()["total_payment"] == "0.00"

    # 2. Payment ₹200
    tx2 = await async_client.post(
        "/api/v1/transactions",
        json={
            "customer_id": cust_id,
            "amount": 200.00,
            "type": "PAYMENT",
            "description": "UPI partial payment",
        },
    )
    assert tx2.status_code == 201

    # Check balance after Payment 1
    c2 = await async_client.get(f"/api/v1/customers/{cust_id}")
    assert c2.json()["outstanding_balance"] == "300.00"
    assert c2.json()["total_credit"] == "500.00"
    assert c2.json()["total_payment"] == "200.00"

    # 3. Credit ₹300
    tx3 = await async_client.post(
        "/api/v1/transactions",
        json={
            "customer_id": cust_id,
            "amount": 300.00,
            "type": "CREDIT",
            "description": "Mustard oil 2L",
        },
    )
    assert tx3.status_code == 201

    # Final Balance Check: 500 - 200 + 300 = 600.00
    c3 = await async_client.get(f"/api/v1/customers/{cust_id}")
    final_data = c3.json()
    assert final_data["outstanding_balance"] == "600.00"
    assert final_data["total_credit"] == "800.00"
    assert final_data["total_payment"] == "200.00"
    assert final_data["transaction_count"] == 3


@pytest.mark.asyncio
async def test_reject_zero_and_negative_amounts(async_client: AsyncClient):
    cust = await async_client.post(
        "/api/v1/customers", json={"name": "Anita Sharma"}
    )
    cid = cust.json()["id"]

    # Test Zero Amount
    res_zero = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 0.00, "type": "CREDIT"},
    )
    assert res_zero.status_code == 422 or res_zero.status_code == 400

    # Test Negative Amount
    res_neg = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": -50.00, "type": "CREDIT"},
    )
    assert res_neg.status_code == 422 or res_neg.status_code == 400


@pytest.mark.asyncio
async def test_reject_payment_exceeding_balance(async_client: AsyncClient):
    cust = await async_client.post(
        "/api/v1/customers", json={"name": "Vijay Rao"}
    )
    cid = cust.json()["id"]

    # Customer has ₹0 balance. Attempting ₹100 payment should fail.
    res1 = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 100.00, "type": "PAYMENT"},
    )
    assert res1.status_code == 400
    err1 = res1.json()
    assert err1["error"]["code"] == "PAYMENT_EXCEEDS_BALANCE"

    # Give ₹250 credit
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 250.00, "type": "CREDIT"},
    )

    # Attempt to pay ₹300 (exceeds balance of ₹250)
    res2 = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 300.00, "type": "PAYMENT"},
    )
    assert res2.status_code == 400
    err2 = res2.json()
    assert err2["error"]["code"] == "PAYMENT_EXCEEDS_BALANCE"

    # Pay exact ₹250 (should succeed)
    res3 = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 250.00, "type": "PAYMENT"},
    )
    assert res3.status_code == 201


@pytest.mark.asyncio
async def test_reject_nonexistent_customer(async_client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": fake_id, "amount": 150.00, "type": "CREDIT"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


@pytest.mark.asyncio
async def test_customer_transaction_history(async_client: AsyncClient):
    cust = await async_client.post(
        "/api/v1/customers", json={"name": "Pooja Singh"}
    )
    cid = cust.json()["id"]

    # Add 2 transactions
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 100.00, "type": "CREDIT", "description": "Item 1"},
    )
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 50.00, "type": "PAYMENT", "description": "Cash"},
    )

    # Retrieve customer transactions
    history_res = await async_client.get(f"/api/v1/customers/{cid}/transactions")
    assert history_res.status_code == 200
    history = history_res.json()
    assert history["total"] == 2
    assert len(history["items"]) == 2
    assert history["items"][0]["amount"] == "50.00"
    assert history["items"][1]["amount"] == "100.00"


@pytest.mark.asyncio
async def test_duplicate_submission_idempotency(async_client: AsyncClient):
    cust = await async_client.post(
        "/api/v1/customers", json={"name": "Karan Johar"}
    )
    cid = cust.json()["id"]

    idempotency_key = "unique_client_token_9999"

    # First submission
    res1 = await async_client.post(
        "/api/v1/transactions",
        json={
            "customer_id": cid,
            "amount": 750.00,
            "type": "CREDIT",
            "idempotency_key": idempotency_key,
        },
    )
    assert res1.status_code == 201
    tx_id_1 = res1.json()["id"]

    # Duplicate submission with same key
    res2 = await async_client.post(
        "/api/v1/transactions",
        json={
            "customer_id": cid,
            "amount": 750.00,
            "type": "CREDIT",
            "idempotency_key": idempotency_key,
        },
    )
    assert res2.status_code == 201
    tx_id_2 = res2.json()["id"]

    # Must return identical transaction without duplicating
    assert tx_id_1 == tx_id_2

    # Verify balance was only credited once (₹750, not ₹1500)
    c = await async_client.get(f"/api/v1/customers/{cid}")
    assert c.json()["outstanding_balance"] == "750.00"
    assert c.json()["transaction_count"] == 1


@pytest.mark.asyncio
async def test_dashboard_summary_calculations(async_client: AsyncClient):
    # Get initial dashboard
    initial_dash = await async_client.get("/api/v1/dashboard/summary")
    assert initial_dash.status_code == 200

    # Add customer and credit
    c = await async_client.post(
        "/api/v1/customers", json={"name": "Deepak Trader"}
    )
    cid = c.json()["id"]
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 1200.00, "type": "CREDIT"},
    )
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid, "amount": 400.00, "type": "PAYMENT"},
    )

    dash = await async_client.get("/api/v1/dashboard/summary")
    assert dash.status_code == 200
    summary = dash.json()
    assert summary["total_customers"] >= 1
    assert Decimal(summary["total_outstanding_credit"]) >= Decimal("800.00")
    assert Decimal(summary["today_credit"]) >= Decimal("1200.00")
    assert Decimal(summary["today_payments"]) >= Decimal("400.00")
    assert len(summary["recent_transactions"]) > 0


@pytest.mark.asyncio
async def test_customer_deletion_protection(async_client: AsyncClient):
    # Customer without transactions CAN be deleted
    c1 = await async_client.post(
        "/api/v1/customers", json={"name": "Temporary Customer"}
    )
    cid1 = c1.json()["id"]
    del_res1 = await async_client.delete(f"/api/v1/customers/{cid1}")
    assert del_res1.status_code == 204

    # Customer WITH transactions CANNOT be deleted
    c2 = await async_client.post(
        "/api/v1/customers", json={"name": "Protected Customer"}
    )
    cid2 = c2.json()["id"]
    await async_client.post(
        "/api/v1/transactions",
        json={"customer_id": cid2, "amount": 100.00, "type": "CREDIT"},
    )
    del_res2 = await async_client.delete(f"/api/v1/customers/{cid2}")
    assert del_res2.status_code == 400
    err = del_res2.json()
    assert err["error"]["code"] == "CUSTOMER_HAS_TRANSACTIONS"


@pytest.mark.asyncio
async def test_concurrent_transaction_consistency(async_client: AsyncClient):
    """Test that multiple concurrent credit additions execute cleanly without race conditions."""
    cust = await async_client.post(
        "/api/v1/customers", json={"name": "Concurrent Tester"}
    )
    cid = cust.json()["id"]

    async def add_credit(amount: float, key: str):
        return await async_client.post(
            "/api/v1/transactions",
            json={
                "customer_id": cid,
                "amount": amount,
                "type": "CREDIT",
                "idempotency_key": key,
            },
        )

    # Dispatch 5 simultaneous credit transactions of ₹100 each
    tasks = [add_credit(100.00, f"conc_key_{i}") for i in range(5)]
    results = await asyncio.gather(*tasks)

    for r in results:
        assert r.status_code == 201

    # Verify total is exactly ₹500.00
    c = await async_client.get(f"/api/v1/customers/{cid}")
    assert c.json()["outstanding_balance"] == "500.00"
    assert c.json()["transaction_count"] == 5
