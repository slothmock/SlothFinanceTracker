import asyncio
from dataclasses import asdict
import json
import aiofiles, os, logging
from datetime import datetime

from PySide6.QtCore import Signal

from app.helpers.strings import EXPENSES_FILE
from app.models.abstract_model import AbstractModel
from app.models.structs import Card, Transaction

class FiatModel(AbstractModel):
    data_changed = Signal()  # Signal for updating UI
    cash_updated = Signal(float)  # Signal for cash updates
    cards_updated = Signal(float)  # Signal for card updates

    def __init__(self, data=None):
        super().__init__(
            headers=["Source", "Date", "Name", "Description", "Amount", "Type"],
            data=data or []
        )
        self.total_cash = 0.0
        self.cards: list[Card] = []  # List of Card objects
        self.total_cards = 0.0
        self.total_funds = 0.0

    def add_transaction(self, transaction: Transaction):
        """
        Add a new transaction.
        """
        self._data.append(transaction)
        self.update_data(self._data)  # Ensure table updates

    def update_cash(self, new_balance):
        """
        Update the total cash balance.
        """
        self.add_transaction(Transaction(
            source="Cash",
            date=datetime.now().strftime("%d-%m-%Y"),
            name="Cash Update",
            description=f"Updated cash balance to £{new_balance:.2f}",
            amount=new_balance - self.total_cash,
            type="Cash Update"
        ))
        asyncio.create_task(self.save_to_file())

        self.total_cash = new_balance
        self.total_funds += new_balance
        self.cash_updated.emit(new_balance)
        self.data_changed.emit()

    def update_cards(self, updated_cards):
        """
        Update card balances.

        Args:
            updated_cards (list): List of updated Card objects or dictionaries.
        """
        try:
            # Ensure compatibility with dict or dataclass
            total_cards_balance = sum(card.balance for card in updated_cards)

            # Add a transaction to track card balance updates
            self.add_transaction(Transaction(
                Source="Cards",
                Date=datetime.now().strftime("%d-%m-%Y"),
                Name="Card Balances Update",
                Description=f"Updated total card balance to £{total_cards_balance:.2f}",
                Amount=f"£{total_cards_balance - self.total_cards:.2f}",
                Type="Cards Update"
            ))
            asyncio.create_task(self.save_to_file())

            self.cards = updated_cards
            self.total_cards = total_cards_balance
            self.cards_updated.emit(total_cards_balance)
            self.data_changed.emit()

        except Exception as e:
            logging.exception(f"Error updating card balances: {e}")

    async def load_from_file(self, filepath=EXPENSES_FILE):
        """
        Load data (transactions, cash balance, cards) from a JSON file.
        """
        try:
            if not os.path.exists(filepath):
                # Create an empty file with the necessary structure
                async with aiofiles.open(filepath, mode="w") as file:
                    empty_data = {
                        "cash": 0.0,
                        "cards": [],
                        "transactions": []
                    }
                    await file.write(json.dumps(empty_data, indent=4))

            async with aiofiles.open(filepath, mode="r") as file:
                content = await file.read()
                if not content:
                    return
                
                data = json.loads(content)

                # Load cash balance
                self.total_cash = data.get("cash", 0.0)
                self.cash_updated.emit(self.total_cash)

                # Load card balances
                self.cards = [Card(**card) for card in data.get("cards", [])]
                self.total_cards = sum(card.balance for card in self.cards)
                self.cards_updated.emit(self.total_cards)

                # Load transactions
                transactions = [
                    Transaction(**txn) for txn in data.get("transactions", [])
                ]
                self.update_data(transactions)
        except Exception as e:
            logging.exception(f"Error loading data from file: {e}")

    async def save_to_file(self, filepath=EXPENSES_FILE):
        """
        Save data (transactions, cash balance, cards) to a JSON file.
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            async with aiofiles.open(filepath, mode="w") as file:
                data = {
                    "cash": self.total_cash,
                    "cards": [asdict(card) for card in self.cards],
                    "transactions": [asdict(txn) for txn in self._data]
                }
                await file.write(json.dumps(data, indent=4))

            logging.info(f"Data saved to {filepath}")
        except Exception as e:
            logging.exception(f"Error saving data to file: {e}")
