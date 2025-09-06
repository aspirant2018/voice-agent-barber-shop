from dotenv import load_dotenv
from typing import Literal

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool,RunContext

from livekit.plugins.turn_detector.multilingual import MultilingualModel
import logging
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
from helpers import send_post
        # The end time is the start time plus 30 minutes
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+    



logger = logging.getLogger(__name__)
load_dotenv()


# Current time in Paris
paris_time = datetime.now(ZoneInfo("Europe/Paris"))

# Format with milliseconds and timezone offset
now = paris_time.isoformat(timespec="milliseconds")
logger.info(f"Now: {now}")
webhook_url = "https://sought-cicada-scarcely.ngrok-free.app/webhook-test/716bf76e-170c-470a-8c9d-82b927292ef9"


system_prompt = f"""
                # Current date and time: {now}

                # Identity:
                You are a helpful barber assistant communicating only in french.
                the barber shop is called "grizzly barbershop".
                The shop is open all days except Sunday, from 10:00 AM to 7:00 PM.
                Your role is to help clients to schedule appointments.

                # Instructions for Booking appointments:
                1. Ask the client for the day and time they would like to book an appointment.
                2. <wait for the client to provide a date and time>.
                3. Check the availability of the requested slot.
                4. If the slot is available, ask for the client's name and the type of service they want.
                5. <wait for the client to provide their name and service type>.
                5. Book the slot and confirm the appointment with the client.
                6. If the slot is not available, ask the client if they would like to choose another slot.

                # Instructions for Cancelling appointments:
                1. Check if the client has an appointment. (You don't need to ask for the phone number, you can get it from the call metadata.)
                2. If the client has an appointment. Confirm the details of the appointment with the client.
                3. Ask the client if they would like to cancel the appointment.
                4. <wait for the client to confirm cancellation>.
                5. Cancel the appointment and confirm the cancellation with the client.
                6. If the client does not have an appointment, inform the client that no appointment was found.


                # clarification techniques:
                  - For spelling: "Could you spell that for me, please?"
                  - For numbers: "Was that 1-5-0-0 or 1-5,000?"
                  - For dates: "So that's January fifteenth, 2023, correct?"

                # People also ask about:
                - Adresses and directions to the barbershop. The adresse is "1 rue d’Hauteville, 75010 Paris" next to Métro Bonne Nouvelle - Ligne 8.

"""
class Assistant(Agent):

    headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
            }
    
    def __init__(self) -> None:
        super().__init__(instructions=system_prompt.format(now=now))

    @function_tool()
    async def on_enter(self) -> None:
        """Handle the on_enter event of the agent."""

        logger.info(f"Enter the on_enter node....")
        logger.info(f"Userdata => {self.session.userdata}")
        userdata = self.session.userdata
        
        instructions = (
            f"Welcome the caller to Grizzly Barbershop, then kindly ask whether the purpose of their call is to schedule an appointment or to inquire about services and prices. "
            )
        
        await self.session.generate_reply(
            instructions = instructions,
            allow_interruptions = False
         )
        


    @function_tool()
    async def check_availability(
        self,
        context: RunContext,
        start_time: str,
    )-> dict:
        
        """Use this tool to check for the  availability of the date and time given by the client."""
        
        await self.session.say(
            "Attendez un instant, je vais vérifier la disponibilité du créneau que vous avez demandé.",
            allow_interruptions=False,
            )
      
        start_time = datetime.fromisoformat(start_time).astimezone(ZoneInfo("Europe/Paris"))    # Convert start_time to a datetime object in the Paris timezone
        end_time = start_time + timedelta(minutes=30)                                           # Add 30 minutes to the start time

        logger.info(f"Start time: {start_time.isoformat(timespec='milliseconds')}")
        logger.info(f"End time: {end_time.isoformat(timespec='milliseconds')}")

        data = {
            "call_time": now,
            "start":start_time.isoformat(),
            "end": end_time.isoformat(),
        }

        response = await send_post(
            webhook_url=webhook_url,
            headers=self.headers,
            tool_name="check_availability",
            data=data
            )


        return {"message": response}
    
    @function_tool()
    async def book_slot(
          self,
          context: RunContext,
          name: str,
          start_time: str,
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

        caller_phone_number = context.session.userdata.phone_number
        logger.info(f"Caller phone number: {caller_phone_number}")
        logger.info(f"Booking slot for {name} on {start_time} in category {category}")
        
        start_time = datetime.fromisoformat(start_time).astimezone(ZoneInfo("Europe/Paris"))    # Convert start_time to a datetime object in the Paris timezone
        end_time = start_time + timedelta(minutes=30)                                           # Add 30 minutes to the start time

        logger.info(f"Start time: {start_time.isoformat(timespec='milliseconds')}")
        logger.info(f"End time: {end_time.isoformat(timespec='milliseconds')}")


        # Extract date and times separately
        date = start_time.date()                 # e.g. 2025-09-06
        start = start_time.time()           # e.g. 14:30:00
        end = end_time.time()               # e.g. 15:00:00

        logger.info(f"Date: {date}, Start time: {start_time}, End time: {end_time}")
        
        data = {
            "call_time": now,
            "phone_number": caller_phone_number,
            "name": name,
            "category":category,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "date": str(date),
            "start": str(start),
            "end": str(end),
            "status": "confirmed",

        }

        response = await send_post(
            webhook_url=webhook_url,
            headers=self.headers,
            tool_name="book_appointment",
            data=data
            )
        
        logger.info(f"Debug response from webhook: {response}")
        
        return {"message": response}


    @function_tool()
    async def has_appointment(
        self,
        context: RunContext,
    )-> dict:
        """ Use this tool to check the caller has an appointment."""

        caller_phone_number = context.session.userdata.phone_number
        logger.info(f"Caller phone number: {caller_phone_number}")

        data = {
                "call_time": now,
                "phone_number": caller_phone_number,
            }

        response = await send_post(
                webhook_url=webhook_url,
                headers=self.headers,
                tool_name="has_appointment",
                data=data
                )
        

        # update the userdata with the appointment details if any
        logger.info(f"Response from has_appointment: {response}") # type list

        if response and isinstance(response, list) and len(response) > 0:
            for booking in response:
                logger.info(f"Booking: {booking}")
                context.session.userdata.bookings.append(booking)
                
        return context.session.userdata.summarize()


    @function_tool()
    async def cancel_appointment(
        self,
        context: RunContext,
        bookingID:str
    )-> dict:
        """Use this tool to cancel an appointment."""

        userdata = context.session.userdata
        logger.info(f"Userdata in cancel_appointment: {userdata}")



        data = {
                "bookingID": bookingID,
                "phone_number": context.session.userdata.phone_number,
            }
        
        logger.info(f"Data to send to webhook: {data}")

        response = await send_post(
                webhook_url=webhook_url,
                headers=self.headers,
                tool_name="cancel_appointment",
                data=data
                )


        return response


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
