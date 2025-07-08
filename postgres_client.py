import psycopg
from enum import Enum
from datetime import datetime, timezone
from config import get_logger, POSTGRES_CONN_URI

logger = get_logger(__name__)

class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    IDLE = "idle"

class PostgresClient:
    def __init__(self):
        try:
            # Quick test connection at startup
            with psycopg.connect(POSTGRES_CONN_URI) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            logger.info("Successfully connected to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def update_sync_status(self, item_id: str, sync_status: SyncStatus):
        """Update only sync status. This should only be used on failure (e.g. sync_status: FAILED)"""
        query = """
            UPDATE plaid_items
            SET sync_status=%s
            WHERE item_id=%s
        """
        try:
            with psycopg.connect(POSTGRES_CONN_URI) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (sync_status, item_id))
                    conn.commit()
        except psycopg.Error as e:
            logger.error(f"Error updating sync_status for item {item_id}: {e}")
            raise

    def update_plaid_item(self, item_id: str, sync_status: str, cursor: str):
        """Update sync status, last_synced_at, and transaction cursor after a successful job"""
        query = """
            UPDATE plaid_items
            SET sync_status=%s, last_synced_at=%s, transaction_cursor=%s
            WHERE item_id=%s
        """
        now = datetime.now(timezone.utc)
        try:
            with psycopg.connect(POSTGRES_CONN_URI) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (sync_status, now, cursor, item_id))
                    conn.commit()
        except psycopg.Error as e:
            logger.error(f"Error updating plaid item {item_id}: {e}")
            raise
