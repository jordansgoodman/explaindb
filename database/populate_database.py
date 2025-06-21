import os
import sqlite3
import requests

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "chinook.db")
DB_URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"

os.makedirs(DB_DIR, exist_ok=True)

if not os.path.exists(DB_PATH):
    print("Downloading database...")
    response = requests.get(DB_URL)
    with open(DB_PATH, "wb") as f:
        f.write(response.content)
    print("Download complete.")
else:
    print("Database already exists.")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"\nTables in the database:")
for (table,) in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  - {table} ({count} rows)")

conn.close()
