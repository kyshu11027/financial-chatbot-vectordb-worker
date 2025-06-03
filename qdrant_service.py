from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as QdrantHttpClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from langchain_core.documents import Document
from config import get_logger, OPENAI_MODEL_NAME, QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME

logger = get_logger(__name__)

class QdrantClient:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=OPENAI_MODEL_NAME)
        self.qdrant_client = QdrantHttpClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        self.vector_store = QdrantVectorStore(
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=self.embeddings,
            client=self.qdrant_client
        )

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


    def save_vector(self, texts: list[str], metadatas: list[dict]):
        """
        Save a batch of texts and metadata into Qdrant.

        Args:
            texts: List of transaction summary strings.
            metadatas: List of dicts with metadata, one per text (e.g., user_id, date, amount).
        """
        try:
            documents = [
                Document(page_content=text, metadata=metadata)
                for text, metadata in zip(texts, metadatas)
            ]
            self.vector_store.add_documents(documents)
            logger.info(f"Saved {len(documents)} documents to Qdrant.")
        except Exception as e:
            logger.error(f"Error saving vectors: {e}")
            raise e
        
    def delete_by_transaction_ids(self, transaction_ids: list[str]):
        """
        Delete all vectors where metadata.transaction_id is in the given list of transaction_ids.
        """
        try:
            filter_ = Filter(
                must=[
                    FieldCondition(
                        key="transaction_id",
                        match=MatchAny(any=transaction_ids)
                    )
                ]
            )

            self.qdrant_client.delete(
                collection_name=QDRANT_COLLECTION_NAME,
                points_selector=filter_
            )
            logger.info(f"Deleted vectors with transaction_ids in list: {transaction_ids}")
        except Exception as e:
            logger.error(f"Error deleting vectors with transaction_ids {transaction_ids}: {e}")
            raise
