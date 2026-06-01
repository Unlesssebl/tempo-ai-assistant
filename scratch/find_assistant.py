import sqlite3
import sys

db_path = "data/contacts.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ищем всех в Технотроне, кто может быть полезен
cursor.execute("SELECT * FROM contacts WHERE company LIKE '%Технотрон%'")
rows = cursor.fetchall()

sys.stdout.reconfigure(encoding='utf-8')
print("--- ВСЕ КОНТАКТЫ ТЕХНОТРОНА ---")
for row in rows:
    print(f"ID: {row[0]} | Co: {row[1]} | Dept: {row[2]} | Name: {row[3]} | Pos: {row[4]} | Phone: {row[5]}")

conn.close()
