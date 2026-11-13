import re
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple
from pydantic import BaseModel
from app.models.transaction import TransactionType


class VoiceIntentType(str, Enum):
    ADD_CREDIT = "ADD_CREDIT"
    RECORD_PAYMENT = "RECORD_PAYMENT"
    CHECK_BALANCE = "CHECK_BALANCE"
    DAILY_SUMMARY = "DAILY_SUMMARY"
    CUSTOMER_HISTORY = "CUSTOMER_HISTORY"
    CORRECT_PENDING_ACTION = "CORRECT_PENDING_ACTION"
    CONFIRM_ACTION = "CONFIRM_ACTION"
    CANCEL_ACTION = "CANCEL_ACTION"
    UNKNOWN = "UNKNOWN"


class ParsedIntent(BaseModel):
    intent: VoiceIntentType
    customer_name: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    description: Optional[str] = None
    raw_text: str
    language: str = "en-IN"
    confidence: float = 1.0


class IntentParser:
    """Multilingual Indic Intent Parser for kirana shopkeeper voice commands."""

    # Indic word-number dictionaries
    TAMIL_NUMBER_WORDS = {
        "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
        "ஆறு": 6, "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10,
        "இருபது": 20, "முப்பது": 30, "நாற்பது": 40, "ஐம்பது": 50,
        "அறுபது": 60, "எழுபது": 70, "எண்பது": 80, "தொண்ணூறு": 90,
        "நூறு": 100, "நூற்று": 100,
        "இருநூறு": 200, "இருநூற்று": 200,
        "முந்நூறு": 300, "முந்நூற்று": 300,
        "நாநூறு": 400, "நாநூற்று": 400,
        "ஐந்நூறு": 500, "ஐந்நூற்று": 500,
        "அறுநூறு": 600, "எழுநூறு": 700, "எண்ணூறு": 800, "தொளாயிரம்": 900,
        "ஆயிரம்": 1000,
    }

    HINDI_NUMBER_WORDS = {
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
        "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
        "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50,
        "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
        "सौ": 100, "हज़ार": 1000, "हजार": 1000,
    }

    ENGLISH_NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        "hundred": 100, "thousand": 1000,
    }

    CONFIRMATION_KEYWORDS = {
        "yes", "yeah", "yep", "sure", "correct", "confirm", "proceed", "save", "ok", "okay",
        "haan", "sahi", "theek", "shuru", "pakka",
        "sari", "aam", "seri", "aamaa", "aamanga", "podu",
        "haudu", "sari ide", "houdu",
    }

    CANCELLATION_KEYWORDS = {
        "no", "nope", "cancel", "stop", "abort", "don't", "dont",
        "nahi", "mat", "roko", "radd", "chhod do",
        "vendaam", "vendam", "illai", "illa", "tappu",
        "beda", "bedave", "thappu",
    }

    CREDIT_KEYWORDS = [
        "udhar", "udhaar", "credit", "kadan", "saala", "due", "owed",
        "उधार", "கடன்", "ಸಾಲ", "podu", "likho", "jodo", "diya",
    ]

    PAYMENT_KEYWORDS = [
        "paid", "payment", "received", "jama", "settle", "settled", "cleared",
        "பணம்", "கொடுத்தார்", "வந்தது", "जमा", "दिया", "मिला", "ಪಾವತಿ", "ಕೊಟ್ಟ",
    ]

    BALANCE_KEYWORDS = [
        "balance", "how much", "kitna", "evvalavu", "eshtu", "owe", "owes",
        "बाकी", "कितना", "பாக்கி", "எவ்வளவு", "ಬಾಕಿ", "ಎಷ್ಟು",
    ]

    SUMMARY_KEYWORDS = [
        "summary", "daily", "today", "report", "hisaab", "kanakku",
        "आज", "आज का हिसाब", "தினசரி", "கணக்கு",
    ]

    def parse(self, text: str, language: str = "en-IN") -> ParsedIntent:
        """Parse natural speech text into a structured intent with extracted entities."""
        raw = text.strip()
        lower = raw.lower()

        # 1. Check for Confirmation / Cancellation first (short phrases)
        clean_words = re.findall(r"\b\w+\b", lower)
        if len(clean_words) <= 3:
            for w in clean_words:
                if w in self.CONFIRMATION_KEYWORDS:
                    return ParsedIntent(
                        intent=VoiceIntentType.CONFIRM_ACTION,
                        raw_text=raw,
                        language=language,
                    )
                if w in self.CANCELLATION_KEYWORDS:
                    return ParsedIntent(
                        intent=VoiceIntentType.CANCEL_ACTION,
                        raw_text=raw,
                        language=language,
                    )

        # 2. Check for Correction Intent (e.g. "Ramesh-ku 500 illa, 350", "Not 500, 350", "500 nahi 350")
        correction_match = re.search(
            r"(?:not|illa|illai|nahi|alla)\s*(\d+(?:\.\d{1,2})?)[,\s]+(?:aana|it is|podu|it should be)?\s*(\d+(?:\.\d{1,2})?)",
            lower,
        ) or re.search(
            r"(\d+(?:\.\d{1,2})?)\s*(?:not|illa|illai|nahi|alla)[,\s]+(\d+(?:\.\d{1,2})?)",
            lower,
        )

        if correction_match:
            correct_amount = Decimal(correction_match.group(2))
            customer = self._extract_customer_name(raw)
            return ParsedIntent(
                intent=VoiceIntentType.CORRECT_PENDING_ACTION,
                customer_name=customer,
                amount=correct_amount,
                raw_text=raw,
                language=language,
            )

        # 3. Check for Daily Summary
        if any(k in lower for k in self.SUMMARY_KEYWORDS) and not any(
            k in lower for k in ["rupees", "rs", "₹", "udhar", "paid"]
        ):
            return ParsedIntent(
                intent=VoiceIntentType.DAILY_SUMMARY,
                raw_text=raw,
                language=language,
            )

        # 4. Check for Balance Query (e.g. "How much does Ramesh owe?", "Ramesh-kku evvalavu baaki?")
        if any(k in lower for k in self.BALANCE_KEYWORDS):
            customer = self._extract_customer_name(raw)
            return ParsedIntent(
                intent=VoiceIntentType.CHECK_BALANCE,
                customer_name=customer,
                raw_text=raw,
                language=language,
            )

        # 5. Extract Amount & Customer
        amount = self._extract_amount(raw)
        customer = self._extract_customer_name(raw)

        # 6. Check for Payment vs Credit
        is_payment = any(k in lower for k in self.PAYMENT_KEYWORDS)
        is_credit = any(k in lower for k in self.CREDIT_KEYWORDS)

        if is_payment and amount is not None:
            return ParsedIntent(
                intent=VoiceIntentType.RECORD_PAYMENT,
                customer_name=customer,
                amount=amount,
                transaction_type=TransactionType.PAYMENT,
                raw_text=raw,
                language=language,
            )

        if (is_credit or amount is not None) and amount is not None:
            return ParsedIntent(
                intent=VoiceIntentType.ADD_CREDIT,
                customer_name=customer,
                amount=amount,
                transaction_type=TransactionType.CREDIT,
                raw_text=raw,
                language=language,
            )

        # 7. Customer History query (e.g. "Show Ramesh history", "Ramesh ledger")
        if customer and any(k in lower for k in ["history", "ledger", "transactions", "khata"]):
            return ParsedIntent(
                intent=VoiceIntentType.CUSTOMER_HISTORY,
                customer_name=customer,
                raw_text=raw,
                language=language,
            )

        return ParsedIntent(
            intent=VoiceIntentType.UNKNOWN,
            customer_name=customer,
            amount=amount,
            raw_text=raw,
            language=language,
            confidence=0.3,
        )

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extract decimal monetary amount from text, handling digits, currency symbols, and Indic words."""
        # 1. Regex for numeric digits (e.g. ₹340, 340.50, 200, 340 rupees, etc.)
        digit_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:rupees|rs|rupaye|rooba|roobai)?", text, re.IGNORECASE)
        if digit_match:
            try:
                val = Decimal(digit_match.group(1))
                if val > 0:
                    return val
            except Exception:
                pass

        # 2. Check for Tamil written number words
        tamil_total = 0
        current_hundreds = 0
        found_tamil = False
        for word in text.split():
            clean_word = word.strip(".,!?:;").strip()
            if clean_word in self.TAMIL_NUMBER_WORDS:
                found_tamil = True
                num = self.TAMIL_NUMBER_WORDS[clean_word]
                if num in (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000):
                    current_hundreds += num
                else:
                    tamil_total += num

        if found_tamil:
            total = current_hundreds + tamil_total
            if total > 0:
                return Decimal(str(total))

        # 3. Check for Hindi / English written number words
        english_match = self._parse_words_to_number(text, self.ENGLISH_NUMBER_WORDS)
        if english_match and english_match > 0:
            return Decimal(str(english_match))

        hindi_match = self._parse_words_to_number(text, self.HINDI_NUMBER_WORDS)
        if hindi_match and hindi_match > 0:
            return Decimal(str(hindi_match))

        return None

    def _parse_words_to_number(self, text: str, word_dict: dict) -> Optional[int]:
        total = 0
        current = 0
        found = False
        for word in text.lower().split():
            clean = word.strip(".,!?:;")
            if clean in word_dict:
                found = True
                val = word_dict[clean]
                if val == 100:
                    current = (current if current > 0 else 1) * 100
                elif val == 1000:
                    current = (current if current > 0 else 1) * 1000
                    total += current
                    current = 0
                else:
                    current += val
        total += current
        return total if found and total > 0 else None

    def _extract_customer_name(self, text: str) -> Optional[str]:
        """Extract customer name from phrasing in English, Tanglish, Hinglish, Tamil, Hindi, Kannada."""
        clean = re.sub(r"[?!.,]", "", text).strip()
        words = clean.split()
        if not words:
            return None

        # 1. Indic scripts: Check first word or token
        first_word = words[0]

        # Tamil name with suffix: ரமேஷுக்கு -> ரமேஷ், சுரேஷுக்கு -> சுரேஷ்
        m_tamil = re.match(r"^([\u0B80-\u0BFF]+?)(?:ுக்கு|க்கு|க்கு|கு)$", first_word)
        if m_tamil:
            return m_tamil.group(1).strip()

        # Hindi token: "रमेश को", "रमेश ने"
        if len(words) > 1 and words[1] in ("को", "ने", "का", "के", "की", "से"):
            return words[0].strip()

        # Tamil token: "ரமேஷ் கணக்கில்", "ரமேஷ் கொடுத்தார்"
        if len(words) > 1 and words[1] in ("கணக்கில்", "கொடுத்தார்", "பணம்", "கடன்"):
            return words[0].strip()

        # 2. English / Latin scripts
        patterns = [
            # "Ramesh-ku ...", "Rameshkku ...", "Rameshukku ..."
            r"^([A-Za-z]+)(?:-ku|-kku|ukku|kku|ku)\b",
            # "Ramesh ko ...", "Ramesh ne ...", "Ramesh ka ..."
            r"^([A-Za-z]+)\s+(?:ko|ne|ka|ke|ki)\b",
            # "Ramesh-ge ...", "Rameshige ..."
            r"^([A-Za-z]+)(?:-ge|ige|ge)\b",
            # "Ramesh paid 200 ..."
            r"^([A-Za-z]+)\s+(?:paid|gives|gave|owes|has|credit)\b",
            # "How much does Ramesh owe?"
            r"(?:how much does|how much)\s+([A-Za-z]+)\s+owe",
            # "Add 340 credit to Ramesh"
            r"(?:to|for)\s+([A-Za-z]+)$",
        ]

        for p in patterns:
            m = re.search(p, clean, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                if name.lower() not in (
                    "how", "what", "add", "record", "today", "credit", "debit",
                    "payment", "yesterday", "summary", "please", "can", "give"
                ):
                    return name.capitalize()

        # Fallback: Check if first word is a name (non-stopword)
        if first_word.lower() not in (
            "how", "what", "add", "give", "record", "today", "show", "is", "credit", "paid", "yesterday"
        ):
            candidate = re.sub(r"(-ku|-kku|ukku|kku|ku|-ge|ge)$", "", first_word, flags=re.IGNORECASE)
            return candidate.capitalize() if candidate.isascii() else candidate

        return None


intent_parser = IntentParser()
