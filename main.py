from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import json
from config import get_logger
from kafka_client import KafkaClient
from plaid_client import PlaidClient
from qdrant_service import QdrantClient
from datetime import datetime, timedelta

logger = get_logger(__name__)

# Initialize Services
kafka = KafkaClient()
plaid = PlaidClient()
qdrant = QdrantClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka.setup_consumer()
    asyncio.create_task(consume_messages())
    yield
    kafka.close()

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
    cursor = message_value.get('cursor', None) # Can be either string or None
    logger.debug(f"user_id: {user_id} - access_token: {access_token} - cursor: {cursor}")

    transactions = []
    if cursor is None:
        logger.debug("Running get transactions")
        today = datetime.today()
        start_date = (today - timedelta(days=180)).date()
        end_date = today.date()
        try:
            transactions = plaid.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )

            # RUN TRANSACTIONS/SYNC AND STORE CURSOR IN POSTGRES
        except Exception as e:
            logger.error(f"Exception in get_transactions: {e}", exc_info=True)
            transactions = []
    else:
        logger.debug("Running get transactions")
        transactions, removed, has_more, next_cursor = plaid.sync_transactions(access_token=access_token, cursor=cursor)
        # STORE CURSOR IN POSTGRES
        
    transaction_strings = [] 
    metadata = []

    for transaction in transactions:
        transaction_strings.append(plaid.transaction_to_string(transaction=transaction))
        metadata.append(plaid.transaction_to_metadata(transaction=transaction, user_id=user_id))
    
    try:
        qdrant.save_vector(texts=transaction_strings, metadatas=metadata)
    except Exception as e:
        logger.error(f"Error saving vectors to Qdrant: {e}")

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
            await asyncio.sleep(1)  # Add delay to prevent tight loop on errors


