from dotenv import load_dotenv
from typing import Literal

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool,RunContext
from livekit.plugins import (
    openai,
    elevenlabs,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

system_prompt = """
                You are a helpful barber assistant communicating  only in French
                via voice.
                Your role is to help clients to make appointment.
                After booking a slot send a confirmation email to the user.
                2. Use clarification techniques:
                  - For spelling: "Could you spell that for me, please?"
                  - For numbers: "Was that 1-5-0-0 or 1-5,000?"
                  - For dates: "So that's January fifteenth, 2023, correct?"
"""
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=system_prompt)

    @function_tool()
    async def book_slot(
          self,
          context: RunContext,
          name: str,
          service_type: str,
          slot: str,
          category:str
      ) -> dict:
          """Book a slot for a service.

          Args:
              name: The name of the client.
              service_type: The type of service to book.
              slot: The slot to book.
              category: The category of the service chosen by the client.

          Returns:
              A confirmation message
          """

          return {"success": "Ok"}

    @function_tool()
    async def send_email(
          self,
          context: RunContext,
          to: str,
      ) -> dict:
          """Send an email to a client.

          Args:
              to: The email of the client.

          Returns:
              A confirmation message
          """

          print("send email Tool")

          return {"success": "Ok"}

    @function_tool()
    async def get_availability(
        self,
        context: RunContext,
        date_range:str
    )-> dict:
      """Get availability for a date range.

      Args:
          date_range: The date range to get availability for.

      Returns:
          A list of available slots.
      """
      return {'available_dates':["20/10","25/10","28/10"]}

    @function_tool()
    async def if_has_appointment(
        self,
        context: RunContext,
        name:str
    )-> dict:
      """Check if an appointment exists.

      Args:
          name: The id of the appointment to check.

      Returns:
          A confirmation message.
      """
      return {'has_appointment':True,"appointment_id":"10010202"}


    @function_tool()
    async def cancel_appointment(
        self,
        context: RunContext,
        appointment_id:str
    )-> dict:
      """Cancel an appointment.

      Args:
          appointment_id: The id of the appointment to cancel.

      Returns:
          A confirmation message.
      """

      return {'success':True}

    @function_tool()
    async def haircut_prices(
        self,
        context: RunContext,
        category:Literal["standard_cut", "skin_fade", "beard_trim", "shave", "combo_cut_and_beard"],
    )-> dict:
      """Get haircut prices.

      Args:
          category: The category of the haircut.

      Returns:
          a dictionnary of haircut prices.
      """
      haircut_prices = {
              "standard_cut": '20 euro',
              "skin_fade": '25 euro',
              "beard_trim": '10 euro',
              "shave": '15 euro',
              "combo_cut_and_beard": '30 euro'}



      return haircut_prices[category]


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=openai.STT(language="fr"),
        llm=openai.LLM(model="gpt-4o-mini"),
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

    await session.generate_reply(
        instructions="Greet the user and welcome him to 'The D-Z Barber SHOP' and offer him assistance in making appointment or haircut prices."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))