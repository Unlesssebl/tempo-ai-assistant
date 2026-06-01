import asyncio
import sys
from src.tools.contact_search import ContactSearchTool

async def check():
    tool = ContactSearchTool()
    # Ищем всех сотрудников Технотрона
    res = await tool.search(" ", "ПТФК Технотрон")
    sys.stdout.reconfigure(encoding='utf-8')
    print(res)

if __name__ == "__main__":
    asyncio.run(check())
