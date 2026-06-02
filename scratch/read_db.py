import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://postgres:123456@localhost:5432/itempo")
    rows = await conn.fetch("""
        SELECT session_id, platform, role, message, metadata 
        FROM chat_messages 
        WHERE platform = 'max' 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    print("=== MESSAGES ===")
    for row in rows:
        print(f"session_id: {row['session_id']}, role: {row['role']}, msg: {row['message'][:50]}")
        print(f"metadata: {row['metadata']}")
        print("-" * 40)
        
    users = await conn.fetch("""
        SELECT user_id, platform, last_activity 
        FROM users 
        WHERE platform = 'max'
        LIMIT 10
    """)
    print("=== USERS ===")
    for u in users:
        print(f"user_id: {u['user_id']}, platform: {u['platform']}, last_activity: {u['last_activity']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
