from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import json
from config import get_logger
from kafka_client import KafkaClient
from plaid_client import PlaidClient
from qdrant_service import QdrantClient
from postgres_client import PostgresClient, SyncStatus
from datetime import datetime, timedelta

logger = get_logger(__name__)

# Initialize Services
kafka = KafkaClient()
plaid = PlaidClient()
qdrant = QdrantClient()
postgres = PostgresClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka.setup_consumer()
    asyncio.create_task(consume_messages())
    yield
    kafka.close()
    postgres.close()

app = FastAPI(
    title="Finance Chatbot API",
    description="A FastAPI backend for the finance chatbot application",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

async def process_message(message):
    # Parse the message object
    message_decoded = message.value().decode('utf-8')
    message_value = json.loads(message_decoded)
    user_id = message_value['user_id']
    access_token = message_value['access_token']
    item_id = message_value['item_id']
    cursor = message_value.get('cursor', None) # Can be either string or None
    logger.debug(f"RECEIVED MESSAGE | user_id: {user_id} - access_token: {access_token} - item_id: {item_id} - cursor: {cursor}")

    transactions = []
    next_cursor = ""
    
    try:
        if cursor is None:
            logger.debug("Running get and sync transactions")
            today = datetime.today()
            start_date = (today - timedelta(days=730)).date() # Get all the transactions from the last 2 years
            end_date = today.date()

            transactions = plaid.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            _, _, next_cursor = plaid.sync_transactions(access_token=access_token, cursor="now")
            logger.debug(f"cursor: {next_cursor}")
            

        else:
            logger.debug("Running sync  transactions")

            transactions, removed, next_cursor = plaid.sync_transactions(access_token=access_token, cursor=cursor)
            
            # Remove the deleted transaction IDs from Qdrant
            removed_transaction_ids = [r['transaction_id'] for r in removed]
            if removed_transaction_ids:
                qdrant.delete_by_transaction_ids(removed_transaction_ids)
        if not transactions:
            logger.info("No transactions found to process.")
            return

        transaction_strings = [plaid.transaction_to_string(tx) for tx in transactions]
        metadata = [plaid.transaction_to_metadata(tx, user_id=user_id) for tx in transactions]

        qdrant.save_vectors(texts=transaction_strings, metadatas=metadata)

        # Successfully processed plaid transactions
        postgres.update_plaid_item(item_id=item_id, sync_status=SyncStatus.IDLE, cursor=next_cursor)
        logger.info(f"Processed {len(transactions)} transactions for item_id {item_id}")

    except Exception as e:
        logger.error(f"Error running job: {e}")
        postgres.update_sync_status(item_id=item_id, sync_status=SyncStatus.FAILED)
        return

async def consume_messages():
    while True:
        try:

            msg = kafka.poll_message()
            if msg is not None:
                try:
                    await asyncio.wait_for(process_message(msg), timeout=100)
                except asyncio.TimeoutError:
                    logger.error("Message processing timed out after 100 seconds")
            else:
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            kafka.setup_consumer()
            await asyncio.sleep(2)  # Add delay to prevent tight loop on errors


