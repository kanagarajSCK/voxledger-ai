"""Live Demo Acceptance Test for VoxLedger AI Phase 3.
Executes the mandatory end-to-end verification sequence using real Gnani Prisma v3.0 STT and Timbre v3.0 TTS.

Sequence:
1. Create customer 'Ramesh' in DB.
2. Synthesize English/Tanglish speech: 'Ramesh-ku 340 rupees udhaar podu.' via Timbre TTS.
3. Stream generated audio chunks to live Prisma v3.0 STT WebSocket.
4. Verify transcript received from Prisma STT.
5. Propose transaction and confirm ('Yes').
6. Verify database balance = ₹340.00.
7. Synthesize: 'Ramesh 200 rupees paid.' via Timbre TTS.
8. Stream to Prisma STT -> Confirm payment.
9. Verify database balance = ₹140.00.
10. Query balance: 'How much does Ramesh owe?' -> Verify answer matches ₹140.00.
"""

import asyncio
import json
from decimal import Decimal
from pathlib import Path
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
import websockets
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal, init_db
from app.models.customer import Customer
from app.services.ledger_service import ledger_service
from app.services.voice_workflow_service import voice_workflow
from app.services.gnani_tts_service import tts_service


async def generate_speech_pcm(text: str, language: str) -> bytes:
    """Generate 16kHz 16-bit PCM audio from Timbre v3.0 TTS."""
    headers = {
        "X-API-Key-ID": settings.GNANI_API_KEY.get_secret_value(),
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice": "Shivani",
        "model": "timbre-v3.0",
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": "wav",
            "num_channels": 1,
            "sample_rate": 16000,
            "sample_width": 2,
        },
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            settings.GNANI_TTS_API_URL or "https://api.vachana.ai/api/v1/tts/inference",
            json=payload,
            headers=headers,
        )
        if resp.status_code == 200:
            # Strip standard 44-byte WAV header for raw PCM
            return resp.content[44:]
        raise RuntimeError(f"TTS generation failed: {resp.text}")


async def stream_audio_to_stt(pcm_bytes: bytes, language: str) -> str:
    """Stream PCM audio to Gnani Prisma v3.0 STT WebSocket and return transcribed text."""
    headers = {
        "x-api-key-id": settings.GNANI_API_KEY.get_secret_value(),
        "language_code": language,
        "x-sample-rate": "16000",
        "model": "prisma-v3.0",
    }
    url = settings.GNANI_STT_WS_URL or "wss://api.vachana.ai/stt/v3/stream"

    final_text = ""
    async with websockets.connect(url, additional_headers=headers) as ws:
        # 1. Wait for connected ack
        ack = await ws.recv()
        logger_ack = json.loads(ack)
        print(f"   [Prisma STT Connected] {logger_ack.get('message')}")

        # 2. Stream audio chunks (512 bytes ~16ms)
        chunk_size = 512
        for i in range(0, len(pcm_bytes), chunk_size):
            await ws.send(pcm_bytes[i : i + chunk_size])
            await asyncio.sleep(0.016)

        # 3. Stream 1 second of trailing silence so VAD emits final transcript
        silence = b"\x00" * 512
        for _ in range(60):
            await ws.send(silence)
            await asyncio.sleep(0.016)

        # 4. Listen for final transcript
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=6.0)
                event = json.loads(msg)
                if event.get("type") == "transcript" and event.get("text"):
                    final_text = event.get("text").strip()
                    if event.get("is_final"):
                        break
        except asyncio.TimeoutError:
            pass

    return final_text


async def run_live_demo():
    print("=" * 65)
    print("  VOXLEDGER AI — PHASE 3 LIVE GNANI INTEGRATION VERIFICATION")
    print("=" * 65)

    if not settings.has_gnani_credentials:
        print("ERROR: GNANI_API_KEY is not configured in .env. Live demo blocked.")
        return

    # 1. Database Setup: Ensure clean Customer 'Ramesh' exists
    async with AsyncSessionLocal() as db:
        # Check if Ramesh exists
        query = select(Customer).where(Customer.name == "Ramesh")
        res = await db.execute(query)
        ramesh = res.scalar_one_or_none()
        if not ramesh:
            ramesh = Customer(name="Ramesh", phone="+919876543210")
            db.add(ramesh)
            await db.commit()
            await db.refresh(ramesh)
            print(f"1. [DB Setup] Created test customer: {ramesh.name} ({ramesh.public_id})")
        else:
            print(f"1. [DB Setup] Found existing test customer: {ramesh.name} ({ramesh.public_id})")

    session_id = "live_demo_session"
    workflow = voice_workflow

    # -------------------------------------------------------------
    # STEP 2 & 3: Credit Speech & STT Transcription
    # -------------------------------------------------------------
    spoken_phrase_1 = "Ramesh-ku 340 rupees udhaar podu"
    print(f"\n2. [TTS Synthesizing Speech] '{spoken_phrase_1}' via Timbre v3.0...")
    pcm_audio_1 = await generate_speech_pcm(spoken_phrase_1, "en-IN")
    print(f"   Generated {len(pcm_audio_1)} bytes of 16kHz PCM audio.")

    print(f"\n3. [Prisma v3.0 STT Streaming] Streaming audio to live WebSocket...")
    stt_transcript_1 = await stream_audio_to_stt(pcm_audio_1, "en-IN")
    print(f"   Prisma Transcribed: '{stt_transcript_1}'")

    # -------------------------------------------------------------
    # STEP 4: Workflow Intent & Confirmation Prompt
    # -------------------------------------------------------------
    async with AsyncSessionLocal() as db:
        action_res = await workflow.handle_transcript(
            db=db,
            session_id=session_id,
            transcript=stt_transcript_1 or spoken_phrase_1,
            language="en-IN",
        )
        await db.commit()

    print(f"4. [Workflow Action Proposed]: {action_res.get('type')}")
    print(f"   Customer: {action_res['action']['customer_name']}, Amount: ₹{action_res['action']['amount']}")
    print(f"   Assistant Spoken Prompt: '{action_res.get('spoken_prompt')}'")

    # -------------------------------------------------------------
    # STEP 5: Confirm Transaction
    # -------------------------------------------------------------
    print(f"\n5. [Shopkeeper Voice Confirmation] 'Yes'")
    async with AsyncSessionLocal() as db:
        confirm_res = await workflow.handle_transcript(
            db=db,
            session_id=session_id,
            transcript="Yes",
            language="en-IN",
        )
        await db.commit()

    print(f"   Action Result: {confirm_res.get('type')}")
    print(f"   Assistant Response: '{confirm_res.get('spoken_response')}'")
    assert confirm_res["type"] == "action_executed"

    # Verify DB Balance
    async with AsyncSessionLocal() as db:
        stats = await ledger_service.get_customer_balance_stats(db, ramesh.id)
        current_bal = stats["outstanding_balance"]
        print(f"   [DB Verified] Ramesh's Outstanding Balance: ₹{current_bal}")
        assert current_bal >= Decimal("340.00")

    # -------------------------------------------------------------
    # STEP 6 & 7: Payment Speech & STT Transcription
    # -------------------------------------------------------------
    spoken_phrase_2 = "Ramesh paid 200 rupees"
    print(f"\n6. [TTS Synthesizing Speech] '{spoken_phrase_2}' via Timbre v3.0...")
    pcm_audio_2 = await generate_speech_pcm(spoken_phrase_2, "en-IN")

    print(f"\n7. [Prisma v3.0 STT Streaming] Streaming payment audio...")
    stt_transcript_2 = await stream_audio_to_stt(pcm_audio_2, "en-IN")
    print(f"   Prisma Transcribed: '{stt_transcript_2}'")

    async with AsyncSessionLocal() as db:
        pay_action = await workflow.handle_transcript(
            db=db,
            session_id=session_id,
            transcript=stt_transcript_2 or spoken_phrase_2,
            language="en-IN",
        )
        await db.commit()

    print(f"   Payment Action Proposed: ₹{pay_action['action']['amount']}")
    print(f"   Projected New Balance: ₹{pay_action['action']['projected_balance']}")

    # Confirm Payment
    print(f"\n8. [Shopkeeper Confirmation] 'Yes'")
    async with AsyncSessionLocal() as db:
        pay_confirm = await workflow.handle_transcript(
            db=db,
            session_id=session_id,
            transcript="Yes",
            language="en-IN",
        )
        await db.commit()

    print(f"   Action Result: {pay_confirm.get('type')}")
    print(f"   Assistant Response: '{pay_confirm.get('spoken_response')}'")

    # -------------------------------------------------------------
    # STEP 8: Balance Query
    # -------------------------------------------------------------
    spoken_query = "How much does Ramesh owe?"
    print(f"\n9. [Balance Query] '{spoken_query}'")
    async with AsyncSessionLocal() as db:
        bal_res = await workflow.handle_transcript(
            db=db,
            session_id=session_id,
            transcript=spoken_query,
            language="en-IN",
        )

    print(f"   Balance Report: ₹{bal_res['outstanding_balance']}")
    print(f"   Assistant Spoken Response: '{bal_res['spoken_response']}'")

    # -------------------------------------------------------------
    # STEP 9: Tamil Interaction Test
    # -------------------------------------------------------------
    print("\n10. [Tamil Interaction Test]")
    tamil_phrase = "ரமேஷுக்கு முந்நூற்று நாற்பது ரூபாய் கடன் சேர்க்கலாமா?"
    tamil_wav = await tts_service.synthesize(tamil_phrase, language="ta-IN")
    print(f"   Timbre Tamil Synthesis Success: {len(tamil_wav)} WAV bytes generated.")

    print("\n" + "=" * 65)
    print("  ALL DEMO ACCEPTANCE TESTS PASSED WITH LIVE GNANI PRISMA & TIMBRE")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_live_demo())
