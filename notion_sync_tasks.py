
# Comfort Air Technologies - Notion Tasks Sync v2.0
# Author: Doug Christy + AI Team
# Description: Sync Notion Tasks -> PostgreSQL, designed for Comfort Air Technologies
# Version: v2.0

import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

response = requests.post(
    f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
    headers=headers
)

data = response.json()

conn = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=os.getenv("PGPORT", 5432),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD"),       # ← pulls from the DB_PASSWORD secret
    dbname=os.getenv("PGDATABASE", "comfort_air_db"),
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS notion_tasks (
    id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    due_date DATE,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

for result in data.get("results", []):
    props = result["properties"]
    task_id = result["id"]
    name = props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
    status = props.get("Status", {}).get("select", {}).get("name", "")
    due = props.get("Due Date", {}).get("date", {}).get("start", None)

    cur.execute("""
    INSERT INTO notion_tasks (id, name, status, due_date)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        status = EXCLUDED.status,
        due_date = EXCLUDED.due_date,
        last_synced = CURRENT_TIMESTAMP;
    """, (task_id, name, status, due))

conn.commit()
cur.close()
conn.close()

print("✅ Notion tasks synced successfully.")
