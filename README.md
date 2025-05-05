# Comfort Air Notion Sync Tasks v2.0

## About
Sync Notion tasks to PostgreSQL automatically.

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python notion_sync_tasks.py
```




## Environment Variables (.env)

You’ll need to create a file called `.env` in the project root (or set these in your Actions secrets):

```env
# Notion API
NOTION_TOKEN=your-notion-token-here
NOTION_DATABASE_ID=your-database-id-here

# PostgreSQL connection
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=your_db_password_here
PGDATABASE=comfort_air_db
```
```

## Auto Sync (Coming in v2.1)
GitHub Actions script to automatically sync nightly or on-demand.
