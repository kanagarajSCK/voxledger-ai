import base64
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.customer import Customer
from app.models.transaction import TransactionType
from app.schemas.transaction import TransactionCreate
from app.services.ledger_service import ledger_service
from app.services.intent_parser import intent_parser, VoiceIntentType, ParsedIntent
from app.services.gnani_tts_service import tts_service

logger = logging.getLogger("voxledger.workflow")


class VoiceWorkflowService:
    """Orchestrates end-to-end voice workflows, customer resolution, financial safety checks,
    and spoken feedback generation.
    """

    def __init__(self):
        # In-memory store of active voice session states: session_id -> session_data
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None, language: str = "en-IN") -> Dict[str, Any]:
        sid = session_id or str(uuid.uuid4())
        if sid not in self._sessions:
            self._sessions[sid] = {
                "session_id": sid,
                "language": language,
                "pending_action": None,
                "history": [],
            }
        elif language:
            self._sessions[sid]["language"] = language
        return self._sessions[sid]

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def handle_transcript(
        self,
        db: AsyncSession,
        session_id: str,
        transcript: str,
        language: str = "en-IN",
    ) -> Dict[str, Any]:
        """Process transcribed speech, extract intent, perform safety validations,
        and generate structured actions and spoken audio feedback.
        """
        session = self.get_or_create_session(session_id, language)
        parsed = intent_parser.parse(transcript, language)

        logger.info(
            "Session %s: Parsed intent=%s, customer=%s, amount=%s from '%s'",
            session_id,
            parsed.intent.value,
            parsed.customer_name,
            parsed.amount,
            transcript,
        )

        # 1. Handle CONFIRM_ACTION
        if parsed.intent == VoiceIntentType.CONFIRM_ACTION:
            return await self._execute_pending_action(db, session)

        # 2. Handle CANCEL_ACTION
        if parsed.intent == VoiceIntentType.CANCEL_ACTION:
            return await self._cancel_pending_action(session)

        # 3. Handle CORRECT_PENDING_ACTION (e.g. "Ramesh-ku 500 illa, 350")
        if parsed.intent == VoiceIntentType.CORRECT_PENDING_ACTION:
            return await self._correct_pending_action(db, session, parsed)

        # 4. Handle ADD_CREDIT or RECORD_PAYMENT
        if parsed.intent in (VoiceIntentType.ADD_CREDIT, VoiceIntentType.RECORD_PAYMENT):
            return await self._propose_transaction_action(db, session, parsed)

        # 5. Handle CHECK_BALANCE
        if parsed.intent == VoiceIntentType.CHECK_BALANCE:
            return await self._handle_check_balance(db, session, parsed)

        # 6. Handle DAILY_SUMMARY
        if parsed.intent == VoiceIntentType.DAILY_SUMMARY:
            return await self._handle_daily_summary(db, session)

        # 7. UNKNOWN or unrecognized command
        unknown_msg = self._format_unknown_response(session["language"])
        audio_b64 = await self._synthesize_b64(unknown_msg, session["language"])
        return {
            "type": "unknown_intent",
            "session_id": session_id,
            "raw_text": transcript,
            "spoken_response": unknown_msg,
            "audio_base64": audio_b64,
        }

    async def _propose_transaction_action(
        self, db: AsyncSession, session: Dict[str, Any], parsed: ParsedIntent
    ) -> Dict[str, Any]:
        lang = session["language"]

        # Validate amount
        if not parsed.amount or parsed.amount <= 0:
            prompt = self._format_invalid_amount_prompt(lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "validation_error",
                "message": "Amount must be greater than zero.",
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        # Validate customer
        if not parsed.customer_name:
            prompt = self._format_missing_customer_prompt(lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "validation_error",
                "message": "Customer name is missing from the voice request.",
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        # Resolve customer in DB
        customers = await self._resolve_customers(db, parsed.customer_name)
        if not customers:
            prompt = self._format_customer_not_found_prompt(parsed.customer_name, lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "customer_not_found",
                "customer_name": parsed.customer_name,
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        if len(customers) > 1:
            candidates = [{"id": c.public_id, "name": c.name, "phone": c.phone} for c in customers]
            prompt = self._format_ambiguous_customer_prompt(parsed.customer_name, lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "ambiguous_customer",
                "customer_name": parsed.customer_name,
                "candidates": candidates,
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        target_customer = customers[0]
        stats = await ledger_service.get_customer_balance_stats(db, target_customer.id)
        current_balance = stats["outstanding_balance"]
        tx_type = parsed.transaction_type or (
            TransactionType.PAYMENT if parsed.intent == VoiceIntentType.RECORD_PAYMENT else TransactionType.CREDIT
        )

        # Payment Cap Validation: Payment cannot exceed outstanding balance
        if tx_type == TransactionType.PAYMENT:
            if current_balance <= Decimal("0.00"):
                prompt = self._format_zero_balance_payment_warning(target_customer.name, lang)
                audio_b64 = await self._synthesize_b64(prompt, lang)
                return {
                    "type": "payment_rejected",
                    "reason": "Customer has zero balance",
                    "spoken_response": prompt,
                    "audio_base64": audio_b64,
                }
            if parsed.amount > current_balance:
                prompt = self._format_overpayment_warning(
                    target_customer.name, parsed.amount, current_balance, lang
                )
                audio_b64 = await self._synthesize_b64(prompt, lang)
                return {
                    "type": "payment_rejected",
                    "reason": "Payment exceeds outstanding balance",
                    "spoken_response": prompt,
                    "audio_base64": audio_b64,
                }

        projected_balance = (
            current_balance + parsed.amount
            if tx_type == TransactionType.CREDIT
            else current_balance - parsed.amount
        )

        action_id = f"act_{uuid.uuid4().hex[:12]}"
        pending = {
            "action_id": action_id,
            "customer_id": target_customer.id,
            "customer_public_id": target_customer.public_id,
            "customer_name": target_customer.name,
            "type": tx_type.value,
            "amount": str(parsed.amount),
            "current_balance": str(current_balance),
            "projected_balance": str(projected_balance),
            "description": f"Voice transaction via {lang}",
            "raw_text": parsed.raw_text,
        }

        # Store in session for confirmation
        session["pending_action"] = pending

        # Generate spoken prompt
        spoken_prompt = self._format_action_confirmation_prompt(
            target_customer.name, tx_type, parsed.amount, lang
        )
        audio_b64 = await self._synthesize_b64(spoken_prompt, lang)

        return {
            "type": "action_proposed",
            "action": pending,
            "spoken_prompt": spoken_prompt,
            "audio_base64": audio_b64,
        }

    async def _correct_pending_action(
        self, db: AsyncSession, session: Dict[str, Any], parsed: ParsedIntent
    ) -> Dict[str, Any]:
        lang = session["language"]
        pending = session.get("pending_action")
        if not pending:
            return {
                "type": "no_pending_action",
                "spoken_response": "There is no pending transaction to correct.",
            }

        new_amount = parsed.amount
        if not new_amount or new_amount <= 0:
            return {
                "type": "validation_error",
                "message": "Invalid correction amount.",
            }

        # If customer changed or specified, verify
        if parsed.customer_name and parsed.customer_name.lower() != pending["customer_name"].lower():
            customers = await self._resolve_customers(db, parsed.customer_name)
            if customers:
                pending["customer_id"] = customers[0].id
                pending["customer_public_id"] = customers[0].public_id
                pending["customer_name"] = customers[0].name

        current_bal = Decimal(pending["current_balance"])
        tx_type = TransactionType(pending["type"])

        # Check overpayment if PAYMENT
        if tx_type == TransactionType.PAYMENT and new_amount > current_bal:
            prompt = self._format_overpayment_warning(pending["customer_name"], new_amount, current_bal, lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "payment_rejected",
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        projected = current_bal + new_amount if tx_type == TransactionType.CREDIT else current_bal - new_amount
        pending["amount"] = str(new_amount)
        pending["projected_balance"] = str(projected)

        prompt = self._format_corrected_action_prompt(pending["customer_name"], tx_type, new_amount, lang)
        audio_b64 = await self._synthesize_b64(prompt, lang)

        return {
            "type": "action_proposed",
            "action": pending,
            "spoken_prompt": prompt,
            "audio_base64": audio_b64,
        }

    async def _execute_pending_action(self, db: AsyncSession, session: Dict[str, Any]) -> Dict[str, Any]:
        lang = session["language"]
        pending = session.get("pending_action")
        if not pending:
            prompt = self._format_no_action_to_confirm(lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {
                "type": "no_pending_action",
                "spoken_response": prompt,
                "audio_base64": audio_b64,
            }

        # Clear pending action from session first to prevent race condition replay
        session["pending_action"] = None

        idempotency_key = f"voice_{pending['action_id']}_{uuid.uuid4().hex[:6]}"

        try:
            tx = await ledger_service.record_transaction(
                db=db,
                customer_public_id=pending["customer_public_id"],
                amount=Decimal(pending["amount"]),
                transaction_type=TransactionType(pending["type"]),
                description=pending.get("description"),
                voice_raw_text=pending.get("raw_text"),
                idempotency_key=idempotency_key,
            )

            # Re-fetch customer updated balance
            stats = await ledger_service.get_customer_balance_stats(db, pending["customer_id"])
            new_balance = stats["outstanding_balance"]

            success_prompt = self._format_success_execution_prompt(
                pending["customer_name"],
                TransactionType(pending["type"]),
                Decimal(pending["amount"]),
                new_balance,
                lang,
            )
            audio_b64 = await self._synthesize_b64(success_prompt, lang)

            return {
                "type": "action_executed",
                "transaction": {
                    "id": tx.public_id,
                    "customer_id": pending["customer_public_id"],
                    "customer_name": pending["customer_name"],
                    "amount": str(tx.amount),
                    "type": tx.type.value,
                    "new_balance": str(new_balance),
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                },
                "spoken_response": success_prompt,
                "audio_base64": audio_b64,
            }
        except Exception as e:
            logger.error("Failed to commit confirmed transaction: %s", e)
            error_msg = f"Failed to record transaction: {str(e)}"
            return {"type": "execution_error", "message": error_msg}

    async def _cancel_pending_action(self, session: Dict[str, Any]) -> Dict[str, Any]:
        lang = session["language"]
        pending = session.get("pending_action")
        session["pending_action"] = None
        if not pending:
            return {"type": "no_pending_action", "spoken_response": "No pending action to cancel."}

        prompt = self._format_action_cancelled_prompt(lang)
        audio_b64 = await self._synthesize_b64(prompt, lang)
        return {
            "type": "action_cancelled",
            "action_id": pending["action_id"],
            "spoken_response": prompt,
            "audio_base64": audio_b64,
        }

    async def _handle_check_balance(
        self, db: AsyncSession, session: Dict[str, Any], parsed: ParsedIntent
    ) -> Dict[str, Any]:
        lang = session["language"]
        if not parsed.customer_name:
            prompt = self._format_missing_customer_prompt(lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {"type": "validation_error", "spoken_response": prompt, "audio_base64": audio_b64}

        customers = await self._resolve_customers(db, parsed.customer_name)
        if not customers:
            prompt = self._format_customer_not_found_prompt(parsed.customer_name, lang)
            audio_b64 = await self._synthesize_b64(prompt, lang)
            return {"type": "customer_not_found", "spoken_response": prompt, "audio_base64": audio_b64}

        customer = customers[0]
        stats = await ledger_service.get_customer_balance_stats(db, customer.id)
        bal = stats["outstanding_balance"]

        prompt = self._format_balance_response(customer.name, bal, lang)
        audio_b64 = await self._synthesize_b64(prompt, lang)

        return {
            "type": "balance_report",
            "customer": {"id": customer.public_id, "name": customer.name},
            "outstanding_balance": str(bal),
            "spoken_response": prompt,
            "audio_base64": audio_b64,
        }

    async def _handle_daily_summary(self, db: AsyncSession, session: Dict[str, Any]) -> Dict[str, Any]:
        lang = session["language"]
        summary = await ledger_service.get_dashboard_summary(db)
        prompt = self._format_daily_summary_prompt(
            summary.total_customers,
            summary.today_credit,
            summary.today_payments,
            summary.total_outstanding_credit,
            lang,
        )
        audio_b64 = await self._synthesize_b64(prompt, lang)

        return {
            "type": "daily_summary_report",
            "summary": {
                "total_customers": summary.total_customers,
                "today_credit": str(summary.today_credit),
                "today_payments": str(summary.today_payments),
                "total_outstanding": str(summary.total_outstanding_credit),
            },
            "spoken_response": prompt,
            "audio_base64": audio_b64,
        }

    async def _resolve_customers(self, db: AsyncSession, name: str) -> List[Customer]:
        clean_name = name.strip()
        query = select(Customer).where(
            or_(
                Customer.name.ilike(f"{clean_name}"),
                Customer.name.ilike(f"{clean_name}%"),
                Customer.name.ilike(f"%{clean_name}%"),
            )
        )
        res = await db.execute(query)
        return list(res.scalars().all())

    async def _synthesize_b64(self, text: str, language: str) -> Optional[str]:
        if not tts_service.is_configured:
            return None
        try:
            wav_bytes = await tts_service.synthesize(text, language)
            if wav_bytes:
                return base64.b64encode(wav_bytes).decode("ascii")
        except Exception as e:
            logger.warning("Failed to synthesize speech in workflow: %s", e)
        return None

    # --- Natural Spoken Prompts Formatting ---

    def _format_action_confirmation_prompt(
        self, name: str, tx_type: TransactionType, amount: Decimal, lang: str
    ) -> str:
        amt = f"{amount:.0f}" if amount % 1 == 0 else f"{amount:.2f}"
        if lang == "ta-IN":
            if tx_type == TransactionType.CREDIT:
                return f"{name}-க்கு {amt} ரூபாய் கடன் சேர்க்கலாமா?"
            return f"{name}-யிடம் இருந்து {amt} ரூபாய் வரவு வைக்கலாமா?"
        elif lang == "hi-IN":
            if tx_type == TransactionType.CREDIT:
                return f"क्या {name} के खाते में {amt} रुपये उधार जोड़ना है?"
            return f"क्या {name} से {amt} रुपये जमा दर्ज करना है?"
        elif lang == "kn-IN":
            if tx_type == TransactionType.CREDIT:
                return f"{name} ಖಾತೆಗೆ {amt} ರೂಪಾಯಿ ಸಾಲ ಸೇರಿಸಬೇಕೆ?"
            return f"{name} ರವರಿಂದ {amt} ರೂಪಾಯಿ ಜಮಾ ಮಾಡಬೇಕೆ?"
        else:
            action = "credit" if tx_type == TransactionType.CREDIT else "payment"
            return f"Should I record a {action} of {amt} rupees for {name}?"

    def _format_corrected_action_prompt(
        self, name: str, tx_type: TransactionType, amount: Decimal, lang: str
    ) -> str:
        amt = f"{amount:.0f}" if amount % 1 == 0 else f"{amount:.2f}"
        if lang == "ta-IN":
            return f"தொகை {amt} ரூபாயாக மாற்றப்பட்டது. {name}-க்கு பதிவு செய்யலாமா?"
        elif lang == "hi-IN":
            return f"रकम बदलकर {amt} रुपये कर दी गई है। क्या {name} के लिए दर्ज करें?"
        else:
            return f"Corrected amount to {amt} rupees. Record this for {name}?"

    def _format_success_execution_prompt(
        self, name: str, tx_type: TransactionType, amount: Decimal, new_bal: Decimal, lang: str
    ) -> str:
        amt = f"{amount:.0f}" if amount % 1 == 0 else f"{amount:.2f}"
        bal = f"{new_bal:.0f}" if new_bal % 1 == 0 else f"{new_bal:.2f}"
        if lang == "ta-IN":
            if tx_type == TransactionType.CREDIT:
                return f"{name} கணக்கில் {amt} ரூபாய் கடன் சேர்க்கப்பட்டது. தற்போதைய பாக்கி {bal} ரூபாய்."
            return f"{name} கணக்கில் {amt} ரூபாய் வரவு வைக்கப்பட்டது. தற்போதைய பாக்கி {bal} ரூபாய்."
        elif lang == "hi-IN":
            if tx_type == TransactionType.CREDIT:
                return f"{name} के खाते में {amt} रुपये उधार दर्ज हो गया। नया बाकी {bal} रुपये है।"
            return f"{name} से {amt} रुपये जमा हो गया। नया बाकी {bal} रुपये है।"
        elif lang == "kn-IN":
            return f"{name} ಖಾತೆಗೆ {amt} ರೂಪಾಯಿ ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಾಗಿದೆ. ಪ್ರಸ್ತುತ ಬಾಕಿ {bal} ರೂಪಾಯಿ."
        else:
            action = "credit" if tx_type == TransactionType.CREDIT else "payment"
            return f"{amt} rupees {action} successfully recorded. {name}'s new balance is {bal} rupees."

    def _format_balance_response(self, name: str, bal: Decimal, lang: str) -> str:
        bal_str = f"{bal:.0f}" if bal % 1 == 0 else f"{bal:.2f}"
        if lang == "ta-IN":
            return f"{name} தற்போதைய பாக்கி {bal_str} ரூபாய்."
        elif lang == "hi-IN":
            return f"{name} का कुल बाकी {bal_str} रुपये है।"
        elif lang == "kn-IN":
            return f"{name} ರವರ ಪ್ರಸ್ತುತ ಬಾಕಿ {bal_str} ರೂಪಾಯಿ."
        else:
            return f"{name} currently owes {bal_str} rupees."

    def _format_daily_summary_prompt(
        self, total_cust: int, credit: Decimal, payments: Decimal, out: Decimal, lang: str
    ) -> str:
        cr = f"{credit:.0f}"
        pay = f"{payments:.0f}"
        if lang == "ta-IN":
            return f"இன்று மொத்த கடன் {cr} ரூபாய், வரவு {pay} ரூபாய், {total_cust} வாடிக்கையாளர்கள் உள்ளனர்."
        elif lang == "hi-IN":
            return f"आज का कुल उधार {cr} रुपये और कुल जमा {pay} रुपये है।"
        else:
            return f"Today's total credit is {cr} rupees and collections are {pay} rupees across {total_cust} customers."

    def _format_customer_not_found_prompt(self, name: str, lang: str) -> str:
        if lang == "ta-IN":
            return f"{name} என்ற வாடிக்கையாளர் கிடைக்கவில்லை. முதலில் அவரை சேர்க்கவும்."
        elif lang == "hi-IN":
            return f"{name} नाम का ग्राहक नहीं मिला। कृपया पहले ग्राहक जोड़ें।"
        else:
            return f"Customer {name} not found. Please add the customer first."

    def _format_ambiguous_customer_prompt(self, name: str, lang: str) -> str:
        if lang == "ta-IN":
            return f"{name} என்ற பெயரில் பல வாடிக்கையாளர்கள் உள்ளனர். ஒருவரை தேர்ந்தெடுக்கவும்."
        elif lang == "hi-IN":
            return f"{name} नाम से कई ग्राहक मिले। कृपया सही ग्राहक चुनें।"
        else:
            return f"Multiple customers found matching {name}. Please select one from the list."

    def _format_overpayment_warning(
        self, name: str, amount: Decimal, current_bal: Decimal, lang: str
    ) -> str:
        amt = f"{amount:.0f}"
        bal = f"{current_bal:.0f}"
        if lang == "ta-IN":
            return f"{amt} ரூபாய் செலுத்த முடியாது. {name}-இன் பாக்கி {bal} ரூபாய் மட்டுமே."
        elif lang == "hi-IN":
            return f"{amt} रुपये जमा नहीं हो सकते। {name} का बाकी केवल {bal} रुपये है।"
        else:
            return f"Payment of {amt} rupees exceeds {name}'s outstanding balance of {bal} rupees."

    def _format_zero_balance_payment_warning(self, name: str, lang: str) -> str:
        if lang == "ta-IN":
            return f"{name}-க்கு எந்த பாக்கியும் இல்லை."
        elif lang == "hi-IN":
            return f"{name} का कोई बकाया नहीं है।"
        else:
            return f"{name} has zero outstanding balance. No payment is owed."

    def _format_action_cancelled_prompt(self, lang: str) -> str:
        if lang == "ta-IN":
            return "செயல்பாடு ரத்து செய்யப்பட்டது."
        elif lang == "hi-IN":
            return "लेनदेन रद्द कर दिया गया।"
        else:
            return "Transaction cancelled."

    def _format_no_action_to_confirm(self, lang: str) -> str:
        return "No pending transaction to confirm."

    def _format_invalid_amount_prompt(self, lang: str) -> str:
        if lang == "ta-IN":
            return "தயவுசெய்து சரியான தொகையை குறிப்பிடவும்."
        elif lang == "hi-IN":
            return "कृपया सही रकम बताएं।"
        else:
            return "Please specify a valid amount."

    def _format_missing_customer_prompt(self, lang: str) -> str:
        if lang == "ta-IN":
            return "தயவுசெய்து வாடிக்கையாளர் பெயரை குறிப்பிடவும்."
        elif lang == "hi-IN":
            return "कृपया ग्राहक का नाम बताएं।"
        else:
            return "Please specify the customer name."

    def _format_unknown_response(self, lang: str) -> str:
        if lang == "ta-IN":
            return "மன்னிக்கவும், புரியவில்லை. மீண்டும் சொல்லுங்கள்."
        elif lang == "hi-IN":
            return "माफ़ कीजिए, समझ नहीं आया। कृपया दोबारा बोलें।"
        else:
            return "Sorry, I didn't catch that. Please speak again."


voice_workflow = VoiceWorkflowService()
