# Comfort Air Technologies - Notion Tasks Sync v2.1
# Author: Doug Christy + AI Team
# Description: Sync Notion Tasks → PostgreSQL
# Changelog v2.1: + pagination loop, password pulled from PG env

import os, requests, psycopg2
from dotenv import load_dotenv

load_dotenv(".env")

NOTION_TOKEN  = os.getenv("NOTION_TOKEN")
DATABASE_ID   = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type":  "application/json",
}

# ---------- NEW: pull every page, not just the first 100 ----------
def fetch_all_pages():
    url   = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    resp  = requests.post(url, headers=headers).json()
    items = resp["results"]
    while resp.get("has_more"):
        resp  = requests.post(url, headers=headers,
                              json={"start_cursor": resp["next_cursor"]}).json()
        items.extend(resp["results"])
    return items
# ------------------------------------------------------------------

results = fetch_all_pages()                           # ← replaces response/data

conn = psycopg2.connect(
    host     = os.getenv("PGHOST", "localhost"),
    port     = os.getenv("PGPORT", 5432),
    user     = os.getenv("PGUSER", "postgres"),
    password = os.getenv("PGPASSWORD"),               # pulled from secret
    dbname   = os.getenv("PGDATABASE", "comfort_air_db"),
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

for result in results:                                # ← iterate over full list
    props   = result["properties"]
    task_id = result["id"]
    name    = props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
    status  = props.get("Status", {}).get("select", {}).get("name", "")
    due     = props.get("Due Date", {}).get("date", {}).get("start", None)

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

print(f"✅ Notion tasks synced successfully. Rows processed: {len(results)}")
