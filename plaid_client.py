from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from datetime import datetime
from config import PLAID_ENVIRONMENT, PLAID_CLIENT_ID, PLAID_API_KEY

class PlaidClient:
    def __init__(self):
        configuration = Configuration(
            host=PLAID_ENVIRONMENT,  # or use plaid.Environment.Sandbox
            api_key={
                "clientId": PLAID_CLIENT_ID,
                "secret": PLAID_API_KEY
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def get_transactions(self, access_token: str, start_date: str, end_date: str):
        options = TransactionsGetRequestOptions(count=100, offset=0)
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=options
        )
        response = self.client.transactions_get(request)
        return response.transactions
    
    def sync_transactions(self, access_token: str, cursor: str | None = None):
        """
        Sync transactions incrementally for a user starting from a cursor.
        If cursor is None, it will sync all available transactions initially.
        
        Returns:
          added_transactions: list of newly added transactions
          removed_transactions: list of removed transactions (if any)
          has_more: bool indicating if more pages exist
          next_cursor: cursor string to use for next incremental sync
        """
        request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=cursor,
            options=TransactionsSyncRequestOptions(count=100)
        )
        response = self.client.transactions_sync(request)

        added = response['added']
        removed = response['removed']
        has_more = response['has_more']
        next_cursor = response['next_cursor']

        return added, removed, has_more, next_cursor
    
    def transaction_to_string(self, transaction: dict) -> str:
        """
        Convert a transaction dict to a readable summary string for embedding.

        Example output:
        "Starbucks, $15.67 on 2025-05-30, category: Food and Drink > Coffee Shop, merchant: Seattle WA"
        """
        name = transaction.get("name", "Unknown merchant")
        amount = transaction.get("amount", 0.0)
        date = transaction.get("date", "unknown date")

        # Join categories with " > " if available
        category_list = transaction.get("category", [])
        category_str = " > ".join(category_list) if category_list else "Uncategorized"

        # Location info, fallback gracefully
        location = transaction.get("location", {})
        city = location.get("city", "")
        state = location.get("state", "")
        location_str = f"{city} {state}".strip() if city or state else ""

        # Build summary string
        parts = [f"{name}", f"${amount:.2f}", f"on {date}", f"category: {category_str}"]
        if location_str:
            parts.append(f"merchant location: {location_str}")

        summary = ", ".join(parts)
        return summary
    

    def transaction_to_metadata(self, transaction: dict) -> dict:
        """
        Extract relevant metadata fields from a transaction dictionary
        for storing alongside vector embeddings.
        """
        # Helper to convert date string to unix timestamp (0 if invalid)
        def date_to_unix(date_str: str) -> int:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return int(dt.timestamp())
            except Exception:
                return 0
    
        transaction_id = transaction.get("transaction_id", "")
        account_id = transaction.get("account_id", "")
        user_id = transaction.get("user_id", "")  # You may need to add this if available elsewhere
        
        amount = transaction.get("amount", 0.0)
        date_str = transaction.get("date", "")
        unix_timestamp = date_to_unix(date_str)
        
        # Convert categories list to a single string joined by " > "
        category_list = transaction.get("category", [])
        if isinstance(category_list, list):
            category_str = " > ".join(category_list)
        else:
            category_str = str(category_list) if category_list else ""
    
        merchant_name = transaction.get("name", "")
        pending = transaction.get("pending", False)
        currency = transaction.get("iso_currency_code") or transaction.get("currency") or ""
    
        metadata = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "user_id": user_id,
            "amount": amount,
            "date": date_str,
            "unix_timestamp": unix_timestamp,
            "category": category_str,
            "merchant_name": merchant_name,
            "pending": pending,
            "currency": currency,
        }
        return metadata