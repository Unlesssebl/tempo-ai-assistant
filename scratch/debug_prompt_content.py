import asyncio
import logging
import os
import sys

# Добавляем корень проекта в путь
sys.path.append(os.getcwd())

from src.core.config import Config
from src.agents.orchestrator import AgentOrchestrator

async def diagnose():
    logging.basicConfig(level=logging.INFO)
    cfg = Config.from_env()
    orch = AgentOrchestrator(cfg)
    await orch.initialize()
    
    query = "график обеда бухгалтерии технотрон"
    
    # 1. Симулируем проход по графу
    state = {"query": query, "messages": [], "search_results": [], "user_company": "technotron"}
    
    # Analyze
    analysis = await orch.analyze_query(state)
    state.update(analysis)
    
    # Search
    search_results = await orch.search_documents(state)
    state.update(search_results)
    
    # Dump
    context_block = "\n\n===\n\n".join(state.get("search_results", []))
    print("\n" + "="*50)
    print("CONTEXT BLOCK SENT TO LLM:")
    print("="*50)
    print(context_block)
    print("="*50 + "\n")
    
    # Generate
    answer_state = await orch.generate_answer(state)
    print("LLM ANSWER:")
    print(answer_state["answer"])

if __name__ == "__main__":
    asyncio.run(diagnose())
