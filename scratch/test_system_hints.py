import os
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock required environment variables before importing Config
os.environ["TELEGRAM_TOKEN"] = "mock_telegram_token"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

from src.core.config import Config
from src.rag.retrieval.hybrid_search import HybridSearchService
from src.rag.retrieval.reranker import LLMReranker, RerankerOutput

async def test_system_hints():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Initializing Config...")
    config = Config.from_env()
    
    # 1. Тестируем HybridSearchService
    print("Testing HybridSearchService...")
    hybrid_service = HybridSearchService(config=config)
    hybrid_service._initialized = True
    
    # Подготавливаем тестовые данные в payload_by_id
    hybrid_service.payload_by_id = {
        "doc_num": {
            "id": "doc_num",
            "text": "Отдел находится в кабинет 105",
            "original_text": "Отдел находится в кабинет 105",
            "source": "01_company/locations/map.txt",
            "metadata": {"title": "Карта"}
        },
        "doc_file": {
            "id": "doc_file",
            "text": "Инструкция для сотрудников",
            "original_text": "Инструкция для сотрудников",
            "source": "02_hr/instruction_manual.txt",
            "metadata": {"title": "Инструкция"}
        },
        "doc_both": {
            "id": "doc_both",
            "text": "Пройдите в кабинет 105 для получения пропуска",
            "original_text": "Пройдите в кабинет 105 для получения пропуска",
            "source": "01_company/locations/instruction_manual.txt",
            "metadata": {"title": "Пропуск"}
        }
    }
    
    # Мокаем методы векторного и лексического поиска
    hybrid_service._vector_search = AsyncMock(return_value=[
        {"id": "doc_num", "text": "Отдел находится в кабинет 105", "source": "01_company/locations/map.txt"},
        {"id": "doc_file", "text": "Инструкция для сотрудников", "source": "02_hr/instruction_manual.txt"},
        {"id": "doc_both", "text": "Пройдите в кабинет 105 для получения пропуска", "source": "01_company/locations/instruction_manual.txt"}
    ])
    hybrid_service._bm25_ranking = MagicMock(return_value={
        "doc_num": 0,
        "doc_file": 1,
        "doc_both": 2
    })
    
    # Запрос содержит число "105" (для doc_num) и совпадение с именем файла "instruction_manual" (для doc_file и doc_both)
    query = "Где кабинет 105 instruction manual"
    
    print(f"Running hybrid search for query: '{query}'")
    results = await hybrid_service.search(query=query, limit=3)
    
    # Проверяем начисление system_hints
    doc_num_res = next(r for r in results if r["id"] == "doc_num")
    doc_file_res = next(r for r in results if r["id"] == "doc_file")
    doc_both_res = next(r for r in results if r["id"] == "doc_both")
    
    print("\n--- HYBRID SEARCH VERIFICATION ---")
    print(f"doc_num hints: {doc_num_res['metadata'].get('system_hints')}")
    print(f"doc_file hints: {doc_file_res['metadata'].get('system_hints')}")
    print(f"doc_both hints: {doc_both_res['metadata'].get('system_hints')}")
    
    assert "Содержит искомый номер/кабинет" in doc_num_res["metadata"]["system_hints"]
    assert "Точное совпадение имени файла" in doc_file_res["metadata"]["system_hints"]
    assert "Содержит искомый номер/кабинет" not in doc_file_res["metadata"]["system_hints"]
    
    # В doc_both сработали оба бонуса
    assert "Содержит искомый номер/кабинет" in doc_both_res["metadata"]["system_hints"]
    assert "Точное совпадение имени файла" in doc_both_res["metadata"]["system_hints"]
    
    print("✅ HybridSearchService system_hints verified successfully!")
    
    # 2. Тестируем LLMReranker
    print("\nTesting LLMReranker...")
    reranker = LLMReranker(config=config)
    
    mock_rerank_output = RerankerOutput(order=[0, 1, 2], status="CORRECT")
    
    with patch("src.llm.text.TextLLMService.generate_structured", new_callable=AsyncMock) as mock_gen_struct:
        mock_gen_struct.return_value = mock_rerank_output
        
        # Вызываем rerank_batch
        reranked, status = await reranker.rerank_batch(query=query, documents=results, top_k=3)
        
        # Извлекаем переданный в prompt аргумент
        called_args, called_kwargs = mock_gen_struct.call_args
        prompt_passed = called_kwargs.get("prompt", "")
        
        print("\n--- LLMRERANKER PROMPT VERIFICATION ---")
        print("Prompt passed to LLM:\n")
        print(prompt_passed)
        
        # Проверяем, что правила prompt содержат новое правило 4
        assert "4. ОБЯЗАТЕЛЬНО учитывай системные подсказки" in prompt_passed
        
        # Проверяем форматирование системных подсказок перед текстом документов
        assert "(Подсказка системы: Содержит искомый номер/кабинет) Отдел находится в кабинет 105" in prompt_passed
        assert "(Подсказка системы: Точное совпадение имени файла) Инструкция для сотрудников" in prompt_passed
        
        # Для doc_both должны быть оба через запятую
        assert "(Подсказка системы: Содержит искомый номер/кабинет, Точное совпадение имени файла) Пройдите в кабинет 105" in prompt_passed
        
    print("✅ LLMReranker prompt and output formatting verified successfully!")
    print("\n🎉 ALL TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_system_hints())
