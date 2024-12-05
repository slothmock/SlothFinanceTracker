import csv, aiofiles, logging
from dataclasses import asdict
from cachetools import TTLCache

from app.models.abstract_model import AbstractModel
from app.helpers.strings import DEFI_POS_FILE
from app.helpers.utils import parse_float
from app.models.structs import DefiPosition


class DefiPositionsModel(AbstractModel):
    def __init__(self, data=None):
        super().__init__(
            headers=["Date", "Source", "Pool", "T1 Amount", "T2 Amount", "T1 Value", "T2 Value", "Total Value", "Fees"],
            data=data or []
        )
        self.cache = TTLCache(maxsize=100, ttl=300)  # Cache for storing processed pools

    async def fetch_data(self, filepath=DEFI_POS_FILE):
        """
        Load DeFi positions from a CSV file asynchronously.
        """
        try:
            async with aiofiles.open(filepath, mode="r") as file:
                content = await file.read()
                reader = csv.DictReader(content.splitlines())
                positions = []

                for row in reader:
                    try:
                        position = DefiPosition(
                            Date=row["Date"],
                            Source=row["Source"],
                            Pool=row["Pool"],
                            T1_Amount=f"{parse_float(row.get("T1 Amount")):.4f}",
                            T2_Amount=f"{parse_float(row.get("T2 Amount")):.4f}",
                            T1_Value=f"${parse_float(row.get("T1 Value")):.2f}",
                            T2_Value=f"${parse_float(row.get("T2 Value")):.2f}",
                            Total_Value=f"${parse_float(row.get("T1 Value")) + parse_float(row.get("T2 Value")):.2f}",
                            Fees=f"${parse_float(row.get("Fees")):.2f}",
                        )
                        positions.append(position)
                    except (ValueError, KeyError) as e:
                        logging.error(f"Skipping invalid row in CSV: {row}. Error: {e}")

                self.update_data(positions)
        except FileNotFoundError:
            logging.error(f"File '{filepath}' not found.")
        except Exception as e:
            logging.exception(f"Error reading DeFi CSV: {e}")

    async def calculate_defi_totals(self):
        """
        Calculate total values of DeFi positions and fees.

        Returns:
            dict: A dictionary with total values and fees.
        """
        try:
            unique_pools = set()
            total_value = 0.0
            total_fees = 0.0

            for position in self._data:
                pool = position.Pool
                if pool not in unique_pools:
                    unique_pools.add(pool)
                    pos_value = parse_float(position.Total_Value)
                    total_value += pos_value
                total_fees += parse_float(position.Fees)

            return {"total_value": total_value, "total_fees": total_fees}
        except Exception as e:
            logging.exception(f"Error calculating totals: {e}")
            return {"total_value": 0.0, "total_fees": 0.0}

    async def save_to_csv(self, filepath=DEFI_POS_FILE):
        """
        Save DeFi positions to a CSV file asynchronously.
        """
        try:
            async with aiofiles.open(filepath, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                await file.write(",".join(self.headers) + "\n")  # Write header
                for position in self._data:
                    await file.write(",".join(str(position.get(header, "")) for header in self.headers) + "\n")
            logging.info(f"DeFi positions saved to {filepath}.")
        except Exception as e:
            logging.exception(f"Error saving DeFi positions to CSV: {e}")