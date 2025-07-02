from confluent_kafka import Consumer, KafkaException
from config import get_logger, KAFKA_CONFIG, GROUP_ID, SAVE_TRANSACTIONS_TOPIC

logger = get_logger(__name__)

class KafkaClient:
    def __init__(self):
        self.consumer = None

    def setup_consumer(self):
        consumer_config = {
            **KAFKA_CONFIG,
            'session.timeout.ms': '45000',
            'client.id': 'python-vectordb-client-1',
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
                raise KafkaException(msg.Error())
            return msg
        except KafkaException as e:
            logger.error(f"Kafka error: {e}")
            raise
        except Exception as e:
            logger.exception("Unexpected error in Kafka poll")
            raise

    def close(self):
        if self.consumer:
            self.consumer.close()
