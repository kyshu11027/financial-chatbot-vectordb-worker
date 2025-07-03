import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap.servers': os.getenv('KAFKA_SERVER', ''),
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': os.getenv('KAFKA_USERNAME', ''),
    'sasl.password': os.getenv('KAFKA_PASSWORD', ''),
}

# Kafka Topic
SAVE_TRANSACTIONS_TOPIC = "save_transactions"
GROUP_ID = "vectordb_consumer"

# OpenAI Configuration
OPENAI_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', '')

# Qdrant Configuration
QDRANT_URL = os.getenv('QDRANT_URL', '')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
QDRANT_COLLECTION_NAME = "transactions"

# Plaid Configuration
PLAID_ENVIRONMENT = os.getenv('PLAID_ENVIRONMENT', '')
PLAID_SECRET = os.getenv('PLAID_SECRET', '')
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID', '')

# Postgres Configuration
POSTGRES_CONN_URI = os.getenv('SUPABASE_CONN_URI', '')
ENV = os.getenv('ENV', '')

def get_logger(name):
    """
    Get a logger instance for a specific module.
    Args:
        name (str): The name of the module (usually __name__)
    Returns:
        logging.Logger: A configured logger instance
    """
    # Get log level from environment variable, default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        log_level = 'INFO'
    
    # Configure root logger if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='[%(levelname)s] %(asctime)s |%(name)s| %(message)s'
        )
        
        # Set httpx's logger to WARNING level to reduce noise
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        # Set Uvicorn's logger to WARNING level
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    return logging.getLogger(name)

# Create a logger for the config module itself
logger = get_logger(__name__) 