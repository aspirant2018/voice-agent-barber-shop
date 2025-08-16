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
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()

system_prompt = """
                # Identity:
                You are a helpful barber assistant communicating only in french.
                the barber shop is called "grizzly barbershop".
                the adresse is "1 rue d’Hauteville, 75010 Paris" next to Métro Bonne Nouvelle - Ligne 8.
                The shop is open all days except Sunday, from 10:00 AM to 7:00 PM.
                Your role is to help clients to schedule appointments.

                # Instructions for the assistant:
                1. Ask the client for the day and time they would like to book an appointment.
                2. <wait for the client to provide a date and time>.
                3. Check the availability of the requested slot.
                4. If the slot is available, ask for the client's name and the type of service they want.
                5. <wait for the client to provide their name and service type>.
                5. Book the slot and confirm the appointment with the client.
                6. If the slot is not available, ask the client if they would like to choose another slot.

                # clarification techniques:
                  - For spelling: "Could you spell that for me, please?"
                  - For numbers: "Was that 1-5-0-0 or 1-5,000?"
                  - For dates: "So that's January fifteenth, 2023, correct?"
"""
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=system_prompt)

    @function_tool()
    async def on_enter(context: RunContext) -> None:
        """Handle the on_enter event of the agent."""

        logger.info(f"Enter the on_enter node....")

        
        instructions = (
            f"Welcome the caller to Grizzly Barbershop, then kindly ask whether the purpose of their call is to schedule an appointment or to inquire about services and prices. "
            )
        
        await context.session.generate_reply(
            instructions = instructions,
            allow_interruptions = False
         )
        

    @function_tool()
    async def book_slot(
          self,
          context: RunContext,
          name: str,
          slot: str,
          category:str
      ) -> dict:
        """Book a slot for a service.

          Args:
              name: The name of the client.
              slot: The slot to book.
              category: The category of the service chosen by the client.

          Returns:
              A confirmation message
        """
        logger.info(f"Enter the book_slot node....")

          # API call to book the slot would go here.
        logger.info(f"Booking slot for {name} on {slot} in category {category}")

        webhook = "https://sought-cicada-scarcely.ngrok-free.app/webhook-test/716bf76e-170c-470a-8c9d-82b927292ef9"

        import aiohttp
        import asyncio

        async def fetch_webhook():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(webhook) as response:
                    return await response.json()

        webhook_task = asyncio.create_task(fetch_webhook())
  
        await self.session.generate_reply(
                    instructions="Tell the user we're processing their request."
                )

        # Wait for the webhook result
        data = await webhook_task
        
        logger.info(f"Webhook response: {data}")
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
    async def check_availability(
        self,
        context: RunContext,
    )-> dict:
        """Use this tool to check for the  availability of the date and time given by the client."""
        await context.session.say(
            "Attendez un instant, je vais vérifier la disponibilité du créneau que vous avez demandé.",
            allow_interruptions=False,
            )
      
        # API call to check availability would go here.
        # For the sake of this example, we will return a hardcoded list of available dates
        output = {
            "success": True,
            "requested_slot": {
                "date": "2025-10-20",
                "time": "14:00",
                "status": "unavailable"
            },
            "suggested_slots": [
                {"date": "2025-10-25", "time": "10:00"},
                {"date": "2025-10-28", "time": "16:30"},
                {"date": "2025-10-29", "time": "09:00"}
            ]
        }
        return output


    @function_tool()
    async def has_appointment(
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
