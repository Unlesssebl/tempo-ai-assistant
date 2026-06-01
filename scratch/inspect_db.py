import sqlite3

db_path = "data/contacts.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM contacts WHERE full_name LIKE '%Нуриев%'")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
