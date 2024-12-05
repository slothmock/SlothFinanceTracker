import logging
from abc import ABC, ABCMeta

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal

from app.models.structs import DefiPosition

class QAbstractABCMeta(type(QAbstractTableModel), ABCMeta): # Define a combined metaclass
    '''Combined metaclass to incorporate functionality from PySide6'''
    pass

class AbstractModel(QAbstractTableModel, ABC, metaclass=QAbstractABCMeta):
    data_changed = Signal()
    HEADER_TO_ATTRIBUTE_MAP = {
            # Holding Headers
            "Currency": "Currency",
            "Balance": "Balance",
            "Value": "Value",
            # Defi Headers
            "Date": "Date",
            "Source": "Source",
            "Pool": "Pool",
            "T1 Amount": "T1_Amount",
            "T2 Amount": "T2_Amount",
            "T1 Value": "T1_Value",
            "T2 Value": "T2_Value",
            "Total Value": "Total_Value",
            "Fees": "Fees",
            # Transaction Headers
            "Type": "Type"
        }  # Signal to notify when the model's data changes

    def __init__(self, headers=None, data=None):
        super().__init__()
        self.headers = headers or []
        self._data = data or []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} initialized.")

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        """
        Return data for the given index and role.
        """
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        row = index.row()
        column = index.column()

        # Get the corresponding dataclass attribute
        header = self.headers[column]
        attribute = self.HEADER_TO_ATTRIBUTE_MAP.get(header, None)

        if not attribute:
            self.logger.warning(f"Header '{header}' does not have a corresponding attribute in the dataclass.")
            return ""

        try:
            item = self._data[row]
            return getattr(item, attribute, "")
        except AttributeError:
            self.logger.warning(f"Item {item} does not have attribute '{attribute}'. Returning empty string.")
            return ""


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_data):
        """
        Replace current data with new data and notify the view.
        """
        if new_data is None or not isinstance(new_data, list):
            logging.warning("update_data received invalid data. Defaulting to empty list.")
            new_data = []

        self.beginResetModel()
        self._data = new_data
        self.endResetModel()
        self.logger.info("Data updated.")

    def calculate_total(self, column_key=None, custom_logic=None):
        """
        Generalized total calculation method for dataclasses.

        Args:
            column_key (str): The key (attribute name) of the column to sum up. Defaults to None.
            custom_logic (callable): A custom calculation logic function.

        Returns:
            float | dict: Total value or a custom result.
        """
        if custom_logic:
            try:
                return custom_logic(self._data)
            except Exception as e:
                self.logger.error(f"Error in custom total calculation: {e}")
                return None

        if not column_key or not hasattr(DefiPosition, column_key):
            self.logger.warning(f"Invalid or unspecified column key for total calculation: {column_key}")
            return 0.0

        total = 0.0
        try:
            for item in self._data:
                value = getattr(item, column_key, 0)
                total += value
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Error calculating total for column '{column_key}': {e}")

        return total
