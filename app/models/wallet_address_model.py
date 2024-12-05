import aiohttp, asyncio, logging
from cachetools import TTLCache

from app.models.abstract_model import AbstractModel
from app.helpers.utils import fetch_crypto_price, parse_float, load_credentials, load_settings
from app.models.dataclasses import Holding


class WalletAddressModel(AbstractModel):
    def __init__(self, data=None):
        super().__init__(
            headers=["Currency", "Balance", "Value"],
            data=data or []
        )
        self.cache = TTLCache(maxsize=100, ttl=300)  # Cache for balance and price fetches

    async def fetch_balances(self, user_addr) -> list[Holding]:
        """
        Fetch balances for ETH and watched tokens asynchronously.

        Args:
            user_addr (str): The wallet address to fetch balances for.

        Returns:
            list: List of balances with calculated values.
        """
        credentials = await load_credentials()
        api_key = credentials.get("basescan_api_key", "")
        if not api_key:
            logging.error("BaseScan API key is missing.")
            return []

        settings = await load_settings()
        watchlist = settings.get("watchlist", [])
        balances = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_balance(
                    session,
                    f"https://api.basescan.org/api?module=account&action=balance&address={user_addr}&apikey={api_key}",
                    "ETH",
                    10**18
                )
            ] + [
                self._fetch_balance(
                    session,
                    f"https://api.basescan.org/api?module=account&action=tokenbalance&contractaddress={token['contract_address']}&address={user_addr}&apikey={api_key}",
                    token["name"],
                    token.get("decimals", 10**18),
                )
                for token in watchlist
            ]

            results = await asyncio.gather(*tasks)
            balances.extend(filter(None, results))

        self.update_data(balances)
        return balances

    async def _fetch_balance(self, session, url, name, divisor) -> Holding:
        """
        Fetch balance for a specific token or currency.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            url (str): The API URL to fetch the balance.
            name (str): The name of the token/currency.
            divisor (int): The divisor to scale raw balance values.

        Returns:
            dict: Balance and value data for the token/currency.
        """
        if (cached_data := self.cache.get(name)):
            logging.info(f"Cache hit for {name}.")
            return cached_data

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"Error fetching {name} balance: {response.status}")
                    return None

                data = await response.json()
                if data.get("status") == "1":
                    raw_balance = int(data["result"])
                    balance = raw_balance / divisor
                    price = await fetch_crypto_price(name)
                    result = Holding(
                        Currency=name,
                        Balance=f"{balance:.4f}",
                        Value=f"${balance * price:.2f}"
                    )
                    self.cache[name] = result  # Cache the result
                    return result
        except Exception as e:
            logging.exception(f"Error fetching balance for {name}: {e}")
        return None
    
    async def get_total(self):
        return self.calculate_total(column_key="Value")
