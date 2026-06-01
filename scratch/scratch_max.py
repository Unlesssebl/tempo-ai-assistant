import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("MAX_TOKEN")
base_url = "https://platform-api.max.ru"

async def main():
    headers = {
        "Authorization": token,
        "Accept": "application/json",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Get subscriptions
        print("Fetching subscriptions GET /subscriptions...")
        async with session.get(f"{base_url}/subscriptions") as resp:
            data = await resp.json()
            subscriptions = data.get("subscriptions", [])
            print(f"Found {len(subscriptions)} active subscriptions:")
            for sub in subscriptions:
                print(" - ", sub["url"])

        # 2. Delete all subscriptions
        for sub in subscriptions:
            url_to_delete = sub["url"]
            print(f"\nDeleting subscription DELETE /subscriptions?url={url_to_delete}...")
            async with session.delete(f"{base_url}/subscriptions", params={"url": url_to_delete}) as resp:
                print("Status:", resp.status)
                print("Body:", await resp.text())

        # 3. Fetch subscriptions again
        print("\nFetching subscriptions again GET /subscriptions...")
        async with session.get(f"{base_url}/subscriptions") as resp:
            print("Status:", resp.status)
            print("Body:", await resp.text())

if __name__ == "__main__":
    asyncio.run(main())
