import re
import yaml
from pathlib import Path

data_dir = Path("data")
fixed_count = 0

# Ищем все файлы
for filepath in data_dir.rglob("*.md"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if not content.startswith("---"):
        continue
        
    end_idx = content.find("---", 3)
    if end_idx == -1:
        continue
        
    yaml_content = content[3:end_idx]
    
    # Проверяем на ошибки
    try:
        yaml.safe_load(yaml_content)
        continue # Если всё ок, пропускаем
    except yaml.YAMLError:
        pass # Если сломано - чиним
        
    # Заменяем внешние двойные кавычки на одинарные для полей title, description, company
    # Пример: title: "ООО "АЙТИ"" -> title: 'ООО "АЙТИ"'
    new_yaml = yaml_content
    for field in ["title", "description", "company"]:
        # Регулярка для захвата значения между внешними кавычками
        pattern = rf'^({field}):\s*"(.*)"$'
        replacement = rf"\1: '\2'"
        new_yaml = re.sub(pattern, replacement, new_yaml, flags=re.MULTILINE)
        
    # Записываем обратно
    new_content = "---" + new_yaml + content[end_idx:]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Fixed: {filepath}")
    fixed_count += 1

print(f"\nTotal fixed files: {fixed_count}")
