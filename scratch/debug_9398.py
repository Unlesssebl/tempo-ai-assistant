import sqlite3
import sys

db_path = "data/contacts.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM contacts WHERE id=9398")
row = cursor.fetchone()

sys.stdout.reconfigure(encoding='utf-8')
if row:
    print(f"ID: {row[0]}")
    print(f"Company: {row[1]}")
    print(f"Dept: {row[2]}")
    print(f"Name: {row[3]}")
    print(f"Pos: {row[4]}")
    print(f"Phone: {row[5]}")
conn.close()
