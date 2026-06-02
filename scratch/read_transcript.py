import json
import os

path = r"C:\Users\ntemw1994\.gemini\antigravity-ide\brain\8b125678-9d3a-4a59-8a22-b51b221da0c9\.system_generated\logs\transcript.jsonl"
if not os.path.exists(path):
    print("Transcript not found")
else:
    print("Searching transcript...")
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "max_" in line or "chat_id" in line:
                # Попробуем найти интересные фрагменты
                if "failed to send" in line or "message_created" in line or "recipient" in line:
                    print(line[:300])
                    count += 1
                    if count > 20:
                        break
    print("Done")
