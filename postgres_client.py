import psycopg
from enum import Enum
from psycopg import Connection, Cursor
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
            self.conn: Connection = psycopg.connect(POSTGRES_CONN_URI)
            self.cursor: Cursor = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def update_sync_status(self, item_id: str, sync_status: SyncStatus):
        # Update only sync status. This should only be used on failure (sync_status: failed)
        query = """
            UPDATE plaid_items
            SET sync_status=%s
            WHERE item_id=%s
        """

        try:
            self.cursor.execute(query, (sync_status, item_id))
            self.conn.commit()  # Ensure the change is saved
        except psycopg.Error as e:
            self.conn.rollback()  # Rollback on error to keep DB consistent
            logger.error(f"Error updating last_synced for item {item_id}: {e}")
            raise 

        return
    
    def update_plaid_item(self, item_id: str, sync_status: str, cursor: str):
        # Update when job is finished the current time and sync_status should be "idle"
        query = """
            UPDATE plaid_items
            SET sync_status=%s, last_synced_at=%s, transaction_cursor=%s
            WHERE item_id=%s
        """
        
        now = datetime.now(timezone.utc)

        try:
            self.cursor.execute(query, (sync_status, now, cursor, item_id))
            self.conn.commit()  # Ensure the change is saved
        except psycopg.Error as e:
            self.conn.rollback()  # Rollback on error to keep DB consistent
            logger.error(f"Error updating last_synced for item {item_id}: {e}")
            raise 


    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("PostgreSQL connection closed.")