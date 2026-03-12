import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.messaging import send_message

async def test_send():
    phone = input("Enter the recipient phone number (with country code, e.g., +44...): ")
    message = input("Enter the message to send: ")
    
    print(f"\nAttempting to send message via {os.getenv('MESSAGING_PROVIDER', 'messagebird')}...")
    
    result = await send_message(phone, message)
    
    if result:
        print("\nSUCCESS! API Response:")
        print(result)
    else:
        print("\nFAILED. Check your logs/environment variables.")

if __name__ == "__main__":
    asyncio.run(test_send())
