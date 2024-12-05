from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Holding:
    Currency: str
    Balance: float
    Value: float

@dataclass
class DefiPosition:
    Date: str
    Source: str
    Pool: str
    T1_Amount: float
    T2_Amount: float
    T1_Value: float
    T2_Value: float
    Total_Value: float
    Fees: float

@dataclass
class Card:
    Name: str
    Balance: float

@dataclass
class Transaction:
    Source: str
    Date: str
    Name: str
    Description: str
    Amount: float
    Type: str

    @staticmethod
    def from_row(row):
        """
        Create a Transaction instance from a CSV row.
        """
        try:
            return Transaction(
                source=row[0],
                date=datetime.strptime(row[1], "%d-%m-%Y").strftime("%d-%m-%Y"),
                name=row[2],
                description=row[3],
                amount=float(row[4]),
                type=row[5]
            )
        except (ValueError, IndexError) as e:
            logging.error(f"Error parsing transaction row: {row}. Error: {e}")
            return None

    def to_row(self):
        """
        Convert a Transaction instance to a CSV row.
        """
        return [
            self.source,
            self.date,
            self.name,
            self.description,
            f"{self.amount:.2f}",
            self.type,
        ]