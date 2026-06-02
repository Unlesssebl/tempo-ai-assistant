import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("MAX_TOKEN")
    if not token:
        print("MAX_TOKEN not found in .env")
        return
        
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    user_id = 244451706
    url = f"https://platform-api.max.ru/messages?user_id={user_id}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers=headers,
            json={"text": "Привет! Это тестовое сообщение по user_id.", "format": "html"}
        )
        print(f"POST {url} -> {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
