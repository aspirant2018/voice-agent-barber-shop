
from dotenv import load_dotenv
from typing import Literal

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool,RunContext
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import logging
from agent import Assistant

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=openai.STT(language="fr"),
        llm=openai.LLM(model="gpt-4.1-mini-2025-04-14"),
        tts=openai.TTS(),
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
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))