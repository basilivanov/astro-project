import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.notification import send_bot_notification

async def main():
    print("Testing Notification Service...")
    # Test fake ID (should fail logic or network, but return False)
    # Since we are mocking or running locally without bot container, it might log error
    res = await send_bot_notification(12345, "Test Message")
    print(f"Result for 12345: {res}")

if __name__ == "__main__":
    asyncio.run(main())
