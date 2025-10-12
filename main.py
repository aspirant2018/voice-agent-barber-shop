
from dotenv import load_dotenv
from typing import Literal

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool,RunContext
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
    deepgram,
    cartesia
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import logging
from agent import Assistant
from datetime import datetime
from zoneinfo import ZoneInfo



logger = logging.getLogger(__name__)
load_dotenv()

from dataclasses import dataclass, field

@dataclass
class UserData:
    customer_name: str | None = None
    phone_number: str | None = None
    bookings: list[dict] = field(default_factory=list)


    def summarize(self) -> str:
        data = {
            "customer_name": self.customer_name or "unknown",
            "customer_phone": self.phone_number or "unknown",
            "bookings": self.bookings,
        }
        return str(data)

async def entrypoint(ctx: agents.JobContext):




    userdata = UserData()
    await ctx.connect()


    from livekit import rtc
    participant = await ctx.wait_for_participant(kind=[rtc.ParticipantKind.PARTICIPANT_KIND_SIP])
    logger.info(f"Participant {participant.identity} has joined the room.")
    logger.info(f"Participant metadata:  {participant.metadata}")
    logger.info(f"Participant attribues: {participant.attributes}")
    logger.info(f"Participant sip phoneNumber: {participant.attributes['sip.phoneNumber']}")

    userdata.phone_number = participant.attributes.get('sip.phoneNumber')
    userdata.call_time = datetime.now(ZoneInfo("Europe/Paris"))

    logger.info(f"User data initialized: {userdata.summarize()}")


    session = AgentSession[UserData](
        userdata=userdata,
        stt=deepgram.STT(language="en-US",api_key="189171d012321ba6c54d147d888f0279e6cffc60"),  # Use `language="fr-FR"` for French
        llm=openai.LLM(model="gpt-4.1-mini-2025-04-14"),
        tts=cartesia.TTS(model="sonic-2",voice="71a7ad14-091c-4e8e-a314-022ece01c121",api_key="sk_car_cK1ht1GBLus2zpDz4G7n7i"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name="my-telephony-agent"))