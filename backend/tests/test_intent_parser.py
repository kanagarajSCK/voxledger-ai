from decimal import Decimal
import pytest
from app.services.intent_parser import intent_parser, VoiceIntentType
from app.models.transaction import TransactionType


def test_parse_credit_intents():
    # English
    r1 = intent_parser.parse("Ramesh-ku 340 rupees udhaar podu.", "en-IN")
    assert r1.intent == VoiceIntentType.ADD_CREDIT
    assert r1.customer_name == "Ramesh"
    assert r1.amount == Decimal("340")
    assert r1.transaction_type == TransactionType.CREDIT

    # Hindi
    r2 = intent_parser.parse("रमेश को 340 रुपये उधार दो.", "hi-IN")
    assert r2.intent == VoiceIntentType.ADD_CREDIT
    assert r2.customer_name == "रमेश"
    assert r2.amount == Decimal("340")

    # Tamil
    r3 = intent_parser.parse("ரமேஷுக்கு முந்நூற்று நாற்பது ரூபாய் கடன் போடு.", "ta-IN")
    assert r3.intent == VoiceIntentType.ADD_CREDIT
    assert r3.amount == Decimal("340")


def test_parse_payment_intents():
    # English
    r1 = intent_parser.parse("Ramesh paid 200 rupees.", "en-IN")
    assert r1.intent == VoiceIntentType.RECORD_PAYMENT
    assert r1.customer_name == "Ramesh"
    assert r1.amount == Decimal("200")
    assert r1.transaction_type == TransactionType.PAYMENT

    # Hindi
    r2 = intent_parser.parse("रमेश ने 200 रुपये जमा किए.", "hi-IN")
    assert r2.intent == VoiceIntentType.RECORD_PAYMENT
    assert r2.customer_name == "रमेश"
    assert r2.amount == Decimal("200")


def test_parse_balance_queries():
    r1 = intent_parser.parse("How much does Ramesh owe?", "en-IN")
    assert r1.intent == VoiceIntentType.CHECK_BALANCE
    assert r1.customer_name == "Ramesh"

    r2 = intent_parser.parse("रमेश का कितना बाकी है?", "hi-IN")
    assert r2.intent == VoiceIntentType.CHECK_BALANCE
    assert r2.customer_name == "रमेश"


def test_parse_correction_intent():
    # "Ramesh-ku 500 illa, 350."
    r1 = intent_parser.parse("Ramesh-ku 500 illa, 350.", "en-IN")
    assert r1.intent == VoiceIntentType.CORRECT_PENDING_ACTION
    assert r1.customer_name == "Ramesh"
    assert r1.amount == Decimal("350")

    # "Not 500, 350"
    r2 = intent_parser.parse("Not 500, 350", "en-IN")
    assert r2.intent == VoiceIntentType.CORRECT_PENDING_ACTION
    assert r2.amount == Decimal("350")


def test_parse_confirmation_and_cancellation():
    for word in ["Yes", "Haan", "Sari", "Confirm", "Okay"]:
        res = intent_parser.parse(word, "en-IN")
        assert res.intent == VoiceIntentType.CONFIRM_ACTION

    for word in ["No", "Nahi", "Cancel", "Vendaam", "Beda"]:
        res = intent_parser.parse(word, "en-IN")
        assert res.intent == VoiceIntentType.CANCEL_ACTION


def test_parse_daily_summary():
    r = intent_parser.parse("Today's summary", "en-IN")
    assert r.intent == VoiceIntentType.DAILY_SUMMARY
