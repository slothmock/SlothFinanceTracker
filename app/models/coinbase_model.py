from dataclasses import asdict
import logging
from typing import List
from cachetools import TTLCache

from app.models.abstract_model import AbstractModel
from app.helpers.utils import fetch_crypto_price, load_credentials

from coinbase.rest import RESTClient

from app.models.dataclasses import Holding

class CoinbaseHoldingsModel(AbstractModel):
    def __init__(self, data=None):
        super().__init__(headers=["Currency", "Balance", "Value"], data=data or [])
        self.client = None
        self.cache = TTLCache(maxsize=100, ttl=300)  # Cache up to 100 items, expires after 5 minutes

    async def init_client(self):
        """Initialize the Coinbase client."""
        credentials = await load_credentials()
        api_key = credentials.get("coinbase_api_key", "")
        api_secret = credentials.get("coinbase_api_secret", "")

        if not api_key or not api_secret:
            logging.error("Coinbase API credentials are missing.")
            return None

        self.client = RESTClient(api_key, api_secret)

    async def get_cb_holdings(self) -> List[Holding]:
        """
        Fetch Coinbase holdings and return as a list of dataclass instances.
        """
        try:
            if not self.client:
                await self.init_client()

            if not self.client:
                self.logger.error("Failed to initialize Coinbase client.")
                return []

            accounts = self.client.get_accounts()
            holdings = []
            for account in accounts["accounts"]:
                balance = float(account["available_balance"]["value"])
                currency = account["currency"]
                if balance > 0.0001:  # Skip negligible balances
                    price = await self.get_crypto_price_cached(currency)
                    holding = Holding(
                        Currency=currency,
                        Balance=balance,
                        Value=balance * price,
                    )
                    holdings.append(holding)

            # Update model data
            self.update_data([asdict(h) for h in holdings])
            self.logger.info("Coinbase holdings updated successfully.")
            return holdings

        except Exception as e:
            self.logger.exception(f"Error fetching Coinbase holdings: {e}")
            return []

    async def get_crypto_price_cached(self, currency: str) -> float:
        """
        Fetch cryptocurrency price with caching.
        """
        if currency in self.cache:
            self.logger.debug(f"Cache hit for {currency}")
            return self.cache[currency]

        self.logger.debug(f"Cache miss for {currency}. Fetching new price...")
        price = await fetch_crypto_price(currency)
        if price is not None:
            self.cache[currency] = price
        return price or 0.0

    async def get_total(self):
        return self.calculate_total(column_key="Value")