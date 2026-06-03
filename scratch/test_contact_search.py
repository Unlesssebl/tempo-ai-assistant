import asyncio
from src.core.config import Config
from src.tools.contact_search import ContactSearchTool

async def main():
    config = Config.from_env()
    tool = ContactSearchTool(config)
    
    # 1. Тест обычного поиска по имени
    print("=== Test 1: Search by name 'Иванов' ===")
    res = await tool.search(search_query="Иванов")
    print(res)
    print()

    # 2. Тест поиска по имени + компании
    print("=== Test 2: Search by name 'Иванов' + company 'КМК' ===")
    res = await tool.search(search_query="Иванов", company_filter="КМК")
    print(res)
    print()

    # 3. Тест поиска по телефону
    print("=== Test 3: Search by phone '4100' ===")
    res = await tool.search(exact_phone="4100")
    print(res)
    print()

if __name__ == "__main__":
    asyncio.run(main())
