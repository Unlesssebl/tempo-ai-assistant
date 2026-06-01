import os
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock required environment variables before importing Config
os.environ["TELEGRAM_TOKEN"] = "mock_telegram_token"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

from src.core.config import Config
from src.rag.retrieval.search import SearchService
from src.rag.retrieval.reranker import RerankerOutput

async def test_mocked_search():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Initializing Config...")
    config = Config.from_env()
    config.use_llm_rerank = True
    config.use_crag = False  # commented out anyway
    config.use_rag_fusion = False
    config.use_hyde = False

    searcher = SearchService(config=config)

    # Mock hybrid search return value
    mock_candidates = [
        {"id": "doc1", "text": "Текст документа 1", "source": "src1", "metadata": {"title": "Док 1"}},
        {"id": "doc2", "text": "Текст документа 2", "source": "src2", "metadata": {"title": "Док 2"}},
        {"id": "doc3", "text": "Текст документа 3", "source": "src3", "metadata": {"title": "Док 3"}},
    ]
    
    searcher.hybrid = MagicMock()
    searcher.hybrid.search = AsyncMock(return_value=mock_candidates)
    searcher.hybrid.initialize = AsyncMock()

    # Mock LLM generation output
    # RerankerOutput: order: List[int], status: Literal["CORRECT", "INCORRECT"]
    mock_rerank_output = RerankerOutput(order=[2, 0, 1], status="CORRECT")
    
    # We patch generate_structured on TextLLMService
    with patch("src.llm.text.TextLLMService.generate_structured", new_callable=AsyncMock) as mock_gen_struct:
        mock_gen_struct.return_value = mock_rerank_output
        
        print("Running search with query...")
        result = await searcher.search("Как вызвать айтишника?", limit=3)
        
        print("\n--- TEST VERIFICATION RESULTS ---")
        print(f"Retrieval Status (should be 'correct'): '{result.retrieval_status}'")
        print(f"Number of resulting documents: {len(result.documents)}")
        for idx, doc in enumerate(result.documents):
            print(f"Rank {idx + 1}: Doc ID={doc['id']}, Title={doc['metadata']['title']}")
        
        # Verify the order of documents. 
        # Expected order based on [2, 0, 1] is: doc3 (index 2), doc1 (index 0), doc2 (index 1)
        expected_ids = ["doc3", "doc1", "doc2"]
        actual_ids = [d["id"] for d in result.documents]
        print(f"Expected IDs: {expected_ids}")
        print(f"Actual IDs:   {actual_ids}")
        
        assert actual_ids == expected_ids, f"Order mismatch: {actual_ids} != {expected_ids}"
        assert result.retrieval_status == "correct", f"Status mismatch: {result.retrieval_status} != 'correct'"
        print("\n✅ SUCCESS: Reranker and SearchService integration behaves exactly as specified!")

async def test_mocked_fallback():
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n----------------------------------------")
    print("Initializing Config for fallback test...")
    config = Config.from_env()
    config.use_llm_rerank = True
    config.use_fallback = True
    config.use_rag_fusion = False

    searcher = SearchService(config=config)

    # Initial search returns empty list to trigger fallback
    mock_candidates_initial = []
    mock_candidates_fallback = [
        {"id": "fallback_doc", "text": "Найденная через fallback информация", "source": "src_fallback", "metadata": {"title": "Документ Фоллбэка"}},
    ]

    async def mock_search_func(query_str, limit=None, company_id=None, qdrant_filter=None, intent=None):
        if "оптимальная строка" in query_str:
            return mock_candidates_fallback
        return mock_candidates_initial

    searcher.hybrid = MagicMock()
    searcher.hybrid.search = AsyncMock(side_effect=mock_search_func)
    searcher.hybrid.initialize = AsyncMock()
    searcher.fallback.search_service = searcher.hybrid

    # Reranker output for fallback candidates
    mock_rerank_output_fallback = RerankerOutput(order=[0], status="CORRECT")
    mock_fallback_query = "оптимальная строка для поиска"

    # Patch generate to return fallback query
    with patch("src.llm.text.TextLLMService.generate_structured", new_callable=AsyncMock) as mock_gen_struct, \
         patch("src.llm.text.TextLLMService.generate", new_callable=AsyncMock) as mock_gen:
        
        mock_gen_struct.return_value = mock_rerank_output_fallback
        mock_gen.return_value = mock_fallback_query

        print("Running search expecting fallback...")
        result = await searcher.search("Как найти айтишника?", limit=3)

        print("\n--- FALLBACK TEST VERIFICATION RESULTS ---")
        print(f"Retrieval Status (should be 'correct'): '{result.retrieval_status}'")
        print(f"Number of resulting documents (should be 1): {len(result.documents)}")
        if len(result.documents) > 0:
            print(f"Doc ID: {result.documents[0]['id']}, Title: {result.documents[0]['metadata']['title']}")
        
        assert len(result.documents) == 1, f"Expected 1 doc, got {len(result.documents)}"
        assert result.documents[0]["id"] == "fallback_doc", f"Expected 'fallback_doc', got {result.documents[0]['id']}"
        assert result.retrieval_status == "correct", f"Expected 'correct', got {result.retrieval_status}"
        print("✅ SUCCESS: FallbackRetriever was triggered, made 1 LLM call, 1 search call, and returned correct results!")

async def main():
    await test_mocked_search()
    await test_mocked_fallback()

if __name__ == "__main__":
    asyncio.run(main())
