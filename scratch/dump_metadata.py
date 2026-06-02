import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://postgres:123456@localhost:5432/itempo")
    rows = await conn.fetch("""
        SELECT DISTINCT metadata 
        FROM chat_messages 
        WHERE platform = 'max'
    """)
    print("=== UNIQUE METADATA ===")
    for row in rows:
        print(row['metadata'])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
