from confluent_kafka import Consumer
from config import get_logger, KAFKA_CONFIG, GROUP_ID, SAVE_TRANSACTIONS_TOPIC

logger = get_logger(__name__)

class KafkaClient:
    def __init__(self):
        self.consumer = None

    def setup_consumer(self):
        consumer_config = {
            **KAFKA_CONFIG,
            'session.timeout.ms': '45000',
            'client.id': 'python-client-1',
            'group.id': GROUP_ID,
            'auto.offset.reset': 'latest',
        }
        self.consumer = Consumer(consumer_config)
        self.consumer.subscribe([SAVE_TRANSACTIONS_TOPIC])
        logger.info("Kafka consumer started, waiting for messages...")

    def poll_message(self):
        if self.consumer is None:
            logger.error("Kafka consumer is not initialized.")
            return None
        try:
            msg = self.consumer.poll(0.1)  # Reduced timeout to 100ms to be more responsive
            if msg is None:
                return None
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                return None
            return msg
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            return None

    def close(self):
        if self.consumer:
            self.consumer.close()
