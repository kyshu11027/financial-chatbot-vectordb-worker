import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_response import TransactionsGetResponse
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from datetime import date, datetime, timezone
from config import PLAID_CLIENT_ID, PLAID_SECRET, get_logger
import certifi

logger = get_logger(__name__)

class PlaidClient:
    def __init__(self):
        configuration = Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                "clientId": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET
            },
            ssl_ca_cert=certifi.where()
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def get_transactions(self, access_token: str, start_date: date, end_date: date):    
        all_transactions = []
        count = 500
        offset = 0
        try:
            while True:
                options = TransactionsGetRequestOptions(count=count, offset=offset)
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=options
                )
                response: TransactionsGetResponse = self.client.transactions_get(request)
                transactions = response['transactions']
                all_transactions.extend(transactions)

                if len(all_transactions) >= response['total_transactions']:
                    break   
                offset += len(transactions)
    
            return all_transactions
            
        except Exception as e:
            logger.error(f"Exception in running TransactionsGet: {e}")
            raise e

        
    def sync_transactions(self, access_token: str, cursor: str | None = None):
        # CONVERT THIS TO A WHILE LOOP AND OUTPUT THE REMOVED AND NEW TRANSACTIONS
        """
        Sync transactions incrementally for a user starting from a cursor.
        If cursor is None, it will sync all available transactions initially.
        
        Returns:
          added_transactions: list of newly added transactions
          removed_transactions: list of removed transactions (if any)
          has_more: bool indicating if more pages exist
          next_cursor: cursor string to use for next incremental sync
        """

        added = []
        modified = []
        removed = [] # Removed transaction ids
        next_cursor = ""
        has_more = True

        try:
            while has_more:
                request = TransactionsSyncRequest(
                    access_token=access_token,
                    cursor=cursor,
                )
                response = self.client.transactions_sync(request)

                # Add this page of results
                added.extend(response['added'])
                modified.extend(response['modified'])
                removed.extend(response['removed'])

                has_more = response['has_more']

                # Update cursor to the next cursor
                next_cursor = response['next_cursor']

            return added, removed, next_cursor

        except Exception as e:
            logger.error(f"Exception in running TransactionsSync: {e}")
            raise e
    
    def transaction_to_string(self, transaction: dict) -> str:
        """
        Convert a transaction dict to a readable summary string for embedding.

        Example output:
        "Starbucks, $15.67 on 2025-05-30, category: Food and Drink > Coffee Shop, merchant: Seattle WA"
        """
        amount = transaction.get("amount", "Unknown amount")
        date = transaction.get("date", "unknown date")
        name = transaction.get("name", "")
        merchant_name = transaction.get("merchant_name", "an account")

        personal_finance_category = transaction.get("personal_finance_category", {})
        primary =  personal_finance_category.get("primary", "").replace("_", " ").lower()
        detailed =  personal_finance_category.get("detailed", "").replace("_", " ").lower()

        # Location info, fallback gracefully
        location = transaction.get("location", {})
        city = location.get("city", "")
        state = location.get("state", "")
        location_str = f"{city} {state}".strip() if city or state else ""

        # Build summary string
        parts = []
            
        if merchant_name:
            parts.append(f"Payment of ${amount:.2f} made on {date} toward {merchant_name} named {name}.")
        else:
            parts.append(f"Payment of ${amount:.2f} made on {date} named {name}.")

        if primary:
            parts.append(f"Category: {primary}")
        if detailed:
            parts.append(f"Detailed Category: {detailed}")
        if location_str:
            parts.append(f"Transaction occurred in {location_str}")

        summary = ", ".join(parts)
        return summary
    

    def transaction_to_metadata(self, transaction: dict, user_id: str) -> dict:
        """
        Extract relevant metadata fields from a transaction dictionary
        for storing alongside vector embeddings.
        """
    
        transaction_id = transaction.get("transaction_id", "")
        account_id = transaction.get("account_id", "")
        
        amount = transaction.get("amount", 0.0)
        date = transaction.get("date", "")
        dt = datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)
        # Convert to Unix timestamp (seconds since epoch)
        unix_timestamp = int(dt.timestamp())
        
        personal_finance_category = transaction.get("personal_finance_category", {})
        primary_category =  personal_finance_category.get("primary", "")
    
        name = transaction.get("name", "")
        merchant_name = transaction.get("merchant_name", "")
        currency = transaction.get("iso_currency_code") or transaction.get("currency") or ""
    
        metadata = {
            "user_id": user_id,
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount,
            "date": unix_timestamp,
            "category": primary_category,
            "transaction_name": name,
            "currency": currency,
        }

        if merchant_name:
            metadata['merchant_name'] = merchant_name

        return metadata