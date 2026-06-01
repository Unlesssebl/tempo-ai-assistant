
import asyncio
import sys
from src.tools.rag_search import FilteredRAGTool
from src.models.state import QueryIntent

sys.stdout.reconfigure(encoding='utf-8')

async def test_tool():
    tool = FilteredRAGTool()
    await tool.initialize()
    
    # Имитируем запрос агента
    intent = QueryIntent(
        intent="hr_policy",
        target_company="ПТФК Технотрон",
        is_topic_shift=False
    )
    
    query = "график обеда бухгалтерии технотрон"
    print(f"Calling tool with query: {query}")
    
    result = await tool.search(query, intent)
    
    print("\n--- TOOL RESULT ---")
    if "ничего не найдено" in result:
        print("❌ FAILED: Still nothing found")
    else:
        print("✅ SUCCESS! Found information:")
        print(result[:1000] + "..." if len(result) > 1000 else result)

if __name__ == "__main__":
    asyncio.run(test_tool())
