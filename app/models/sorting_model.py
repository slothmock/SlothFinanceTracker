from datetime import datetime

from PySide6.QtCore import QSortFilterProxyModel

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