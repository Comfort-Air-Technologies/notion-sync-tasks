#!/usr/bin/env python3
import os
import logging
import psycopg2
import requests
import datetime
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_database():
    """Connect to the PostgreSQL database using environment variables."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT")
        )
        logger.info(f"Connected to database: {os.getenv('PGDATABASE')}")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def fetch_tasks_from_notion() -> List[Dict[str, Any]]:
    """Fetch tasks from Notion API."""
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    headers = {"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28"}
    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers
        )
        response.raise_for_status()
        tasks = response.json().get("results", [])
        logger.info(f"Fetched {len(tasks)} tasks from Notion")
        return tasks
    except Exception as e:
        logger.error(f"Failed to fetch tasks from Notion: {e}")
        raise

def sync_notion_tasks(tasks: List[Dict[str, Any]]) -> int:
    """
    Sync Notion tasks to the database.
    
    Args:
        tasks: List of task dictionaries from Notion API
        
    Returns:
        Number of rows processed
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    rows_processed = 0
    
    for task in tasks:
        task_id = task.get('id')
        # Extract task properties from Notion's structure
        name = task["properties"].get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
        status = task["properties"].get("Status", {}).get("status", {}).get("name", "")
        due_date = task["properties"].get("Due Date", {}).get("date", {}).get("start")
        last_synced = datetime.datetime.utcnow()

        logger.info(f"Processing task: ID={task_id}, Name={name}, Status={status}, Due Date={due_date}")

        # Process due date
        if due_date:
            try:
                due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.warning(f"Invalid due_date format for task {task_id}: {due_date}, setting to NULL")
                due_date = None
        else:
            due_date = None

        query = """
        INSERT INTO notion_tasks (id, name, status, due_date, last_synced)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            status = EXCLUDED.status,
            due_date = EXCLUDED.due_date,
            last_synced = EXCLUDED.last_synced
        """
        params = (task_id, name, status, due_date, last_synced)
        try:
            logger.info(f"Executing query: {query % params}")
            cursor.execute(query, params)
            rows_processed += cursor.rowcount
        except Exception as e:
            logger.error(f"Error syncing task {task_id}: {e}")
            conn.rollback()
        else:
            conn.commit()

    logger.info(f"✅ Notion tasks synced successfully. Rows processed: {rows_processed}")
    cursor.close()
    conn.close()
    
    return rows_processed

def main():
    """Main function to fetch and sync Notion tasks."""
    try:
        tasks = fetch_tasks_from_notion()
        rows_processed = sync_notion_tasks(tasks)
        logger.info(f"Total rows processed: {rows_processed}")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
