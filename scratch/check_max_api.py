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
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Попробуем разные эндпоинты, чтобы найти список чатов
        endpoints = ["/chats", "/dialogs", "/conversations", "/me"]
        for ep in endpoints:
            try:
                resp = await client.get(f"https://platform-api.max.ru{ep}", headers=headers)
                print(f"GET {ep} -> {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"Data: {str(data)[:500]}")
                else:
                    print(f"Response: {resp.text[:200]}")
            except Exception as e:
                print(f"Error {ep}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
