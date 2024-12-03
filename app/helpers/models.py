
import csv, aiofiles, aiohttp, asyncio, logging
from datetime import datetime
import os

from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel

from coinbase.rest import RESTClient

from app.helpers.utils import fetch_crypto_price, load_settings, load_credentials, parse_float
from app.helpers.strings import DEFI_POS_FILE


class CoinbaseHoldingsModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self.headers = ["Currency", "Balance", "Value"]
        self._data = data or []
        self.client = None

    async def init_client(self):
        """Initialize the Coinbase client."""
        credentials = await load_credentials()
        api_key = credentials.get("coinbase_api_key", "")
        api_secret = credentials.get("coinbase_api_secret", "")

        if not api_key or not api_secret:
            logging.error("Coinbase API credentials are missing.")
            return None

        self.client = RESTClient(api_key, api_secret)

    async def get_cb_holdings(self):
        """
        Fetch Coinbase holdings.
        Returns:
            list: List of holdings with calculated values.
        """
        try:
            if not self.client:
                await self.init_client()

            if not self.client:
                return []

            accounts = self.client.get_accounts()
            holdings = []
            total_value = 0.0

            for account in accounts["accounts"]:
                balance = float(account["available_balance"]["value"])
                currency = account["currency"]
                if balance > 0.0001:
                    price = await fetch_crypto_price(currency)
                    holdings.append({
                        "Currency": currency,
                        "Balance": f"{balance:.4f}",
                        "Value": f"${balance * price:.2f}",
                    })
                    total_value += balance * price

            return holdings

        except Exception as e:
            logging.exception(f"Error fetching Coinbase holdings: {e}")
            return []

    async def calculate_total(self):
        """Calculate the total portfolio value."""
        return sum(float(item['Value'].replace('$', '')) for item in self._data)

    def update_data(self, new_data):
        """Update internal data and notify view."""
        self.beginResetModel()
        self._data = new_data
        self.sort(0)
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return self._data[index.row()].get(self.headers[index.column()], "")

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        """
        Sort the data by the given column.
        """
        try:
            key = self.headers[column]  # Column to sort by
            reverse = order == Qt.DescendingOrder

            # Sort the _data
            self._data.sort(key=lambda x: self._parse_sort_key(x.get(key, "")), reverse=reverse)
            self.layoutChanged.emit()  # Notify view of layout change
        except Exception as e:
            logging.exception(f"Error sorting data by column {column}: {e}")

    def _parse_sort_key(self, value):
        """
        Helper function to parse the value for sorting.
        """
        try:
            return float(value.replace("$", "").replace(",", "")) if isinstance(value, str) else float(value)
        except ValueError:
            return value  # Fallback to raw value for strings

class DefiPositionsModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self.headers = [
            "Date", "Source", "Pool",
            "T1 Amount", "T2 Amount",
            "T1 Value", "T2 Value",
            "Total Value", "Fees"
        ]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return self._data[index.row()].get(self.headers[index.column()], "")

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_data):
        """Update internal data and notify view."""
        self.beginResetModel()
        self._data = new_data
        self.sort(0)
        self.endResetModel()

    async def fetch_data(self):
        """Fetch DeFi positions from a CSV file."""
        try:
            # Ensure the file exists, create it if it does not
            if not os.path.exists(DEFI_POS_FILE):
                async with aiofiles.open(DEFI_POS_FILE, mode="w") as file:
                    writer = csv.DictWriter(file, fieldnames=[
                        "Date", "Source", "Pool",
                        "T1 Amount", "T2 Amount",
                        "T1 Value", "T2 Value",
                        "Fees", "Total Value"
                    ])
                    writer.writeheader()  # Add header to the new file

            # Open and read the file
            async with aiofiles.open(DEFI_POS_FILE, mode="r") as file:
                content = await file.read()
                reader = csv.DictReader(content.splitlines())
                return [
                    {
                        **row,
                        "T1 Value": f"${parse_float(row.get('T1 Value')):.2f}",
                        "T2 Value": f"${parse_float(row.get('T2 Value')):.2f}",
                        "Fees": f"${parse_float(row.get('Fees')):.2f}",
                        "Total Value": f"${parse_float(row.get('T1 Value')) + parse_float(row.get('T2 Value')):.2f}",
                    }
                    for row in reader
                ]
        except Exception as e:
            logging.exception(f"Error reading or creating DeFi CSV: {e}")
            return []

    async def calculate_total(self):
        """Calculate total value of unique DeFi positions."""
        unique_pools = set()
        total_value = 0.0
        for position in self._data:
            pool = position.get("Pool", "")
            if pool not in unique_pools:
                unique_pools.add(pool)
                total_value += parse_float(position.get("Total Value").replace("$", ""))
        return total_value

    async def calculate_fee_total(self):
        """Calculate the total fee revenue."""
        return sum(parse_float(item["Fees"].replace("$", "")) for item in self._data)

    def sort(self, column, order=Qt.AscendingOrder):
        """
        Sort the data by the given column.
        """
        try:
            key = self.headers[column]  # Column to sort by
            reverse = order == Qt.DescendingOrder

            # Sort the _data
            self._data.sort(key=lambda x: self._parse_sort_key(x.get(key, "")), reverse=reverse)
            self.layoutChanged.emit()  # Notify view of layout change
        except Exception as e:
            logging.exception(f"Error sorting data by column {column}: {e}")

    def _parse_sort_key(self, value):
        """
        Helper function to parse the value for sorting.
        """
        try:
            return float(value.replace("$", "").replace(",", "")) if isinstance(value, str) else float(value)
        except ValueError:
            return value  # Fallback to raw value for strings

class WalletAddressModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self.headers = ["Currency", "Balance", "Value"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return self._data[index.row()].get(self.headers[index.column()], "")

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_data):
        """Update internal data and notify view."""
        self.beginResetModel()
        self._data = new_data
        self.sort(0)
        self.endResetModel()

    async def fetch_balances(self, user_addr):
        """Fetch balances for ETH and watched tokens."""
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
                self._fetch_balance(session, f"https://api.basescan.org/api?module=account&action=balance&address={user_addr}&apikey={api_key}", "ETH", 10**18)
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

        return balances

    async def _fetch_balance(self, session, url, name, divisor):
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
                    return {
                        "Currency": name,
                        "Balance": f"{balance:.4f}",
                        "Value": f"${balance * price:.2f}",
                    }
        except Exception as e:
            logging.exception(f"Error fetching balance for {name}: {e}")
        return None
   
    async def calculate_total(self):
        """
        Calculate the total value of wallet holdings.

        Returns:
            float: Total value of held tokens.
        """
        try:
            return sum(parse_float(item["Value"].replace("$", "")) for item in self._data)
        except Exception as e:
            logging.exception(f"Error calculating total wallet value: {e}")
            return 0.0

    def sort(self, column, order=Qt.AscendingOrder):
        """
        Sort the data by the given column.
        """
        try:
            key = self.headers[column]  # Column to sort by
            reverse = order == Qt.DescendingOrder

            # Sort the _data
            self._data.sort(key=lambda x: self._parse_sort_key(x.get(key, "")), reverse=reverse)
            self.layoutChanged.emit()  # Notify view of layout change
        except Exception as e:
            logging.exception(f"Error sorting data by column {column}: {e}")

    def _parse_sort_key(self, value):
        """
        Helper function to parse the value for sorting.
        """
        try:
            return float(value.replace("$", "").replace(",", "")) if isinstance(value, str) else float(value)
        except ValueError:
            return value  # Fallback to raw value for strings
        
class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        """
        Custom sorting logic for QSortFilterProxyModel.
        """
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)

        # Handle date strings formatted as dd-mm-yyyy
        try:
            left_date = datetime.strptime(left_data, "%d-%m-%Y")
            right_date = datetime.strptime(right_data, "%d-%m-%Y")
            return left_date < right_date
        except ValueError:
            pass  # Not a date, fallback to default sorting

        # Handle numerical strings
        try:
            return float(left_data.replace("$", "").replace(",", "")) < float(
                right_data.replace("$", "").replace(",", "")
            )
        except ValueError:
            pass  # Not a number, fallback to string comparison

        # Default string comparison
        return left_data < right_data