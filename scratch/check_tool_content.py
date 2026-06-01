
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Читаем UTF-16LE файл (результат PowerShell редиректа)
try:
    content = open('scratch/test_rag_tool_output.txt', encoding='utf-16').read()
    
    targets = ["График обедов Технотрон", "Бухгалтерия, ПЭО", "11:00 – 12:00"]
    
    print("--- CHECKING FOR TARGET PHRASES ---")
    for t in targets:
        if t in content:
            print(f"✅ FOUND: '{t}'")
        else:
            print(f"❌ MISSING: '{t}'")
            
except Exception as e:
    print(f"Error: {e}")
