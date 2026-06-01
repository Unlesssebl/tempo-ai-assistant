
import asyncio
from src.tools.rag_search import FilteredRAGTool
from src.models.state import QueryIntent
from src.core.config import Config

async def test_tool():
    config = Config.from_env()
    tool = FilteredRAGTool(config)
    
    # Имитируем запрос агента
    intent = QueryIntent(
        intent="hr_policy",
        target_company="ПТФК Технотрон",
        is_topic_shift=False
    )
    
    query = "график обеда бухгалтерии технотрон"
    print(f"Calling tool with query: {query}")
    
    result = await tool.search(query, intent=intent)
    
    print("\n--- TOOL RESULT ---")
    print(result[:500] + "..." if len(result) > 500 else result)

if __name__ == "__main__":
    asyncio.run(test_tool())
