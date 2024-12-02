from PySide6.QtCore import Qt, QSortFilterProxyModel

class CustomProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_field = None  # The field to filter by
        self.filter_value = None  # The value to filter
        
    def lessThan(self, left, right):
        """
        Override the lessThan method to support numeric sorting.
        """
        left_data = left.data(Qt.DisplayRole)
        right_data = right.data(Qt.DisplayRole)

        try:
            # Attempt to compare as floats
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            # Fall back to string comparison
            return str(left_data) < str(right_data)
    
    def set_filter(self, field, value):
        """
        Set the field and value to filter by.
        """
        self.filter_field = field
        self.filter_value = value.lower() if isinstance(value, str) else value
        self.invalidateFilter()  # Trigger a re-evaluation of the filter

    def filterAcceptsRow(self, source_row, source_parent):
        """
        Override to determine if a row should be shown based on the filter.
        """
        if not self.filter_field or not self.filter_value:
            return True  # No filtering

        model = self.sourceModel()
        index = model.index(source_row, model.headers.index(self.filter_field))
        data = index.data(Qt.DisplayRole)

        # Perform case-insensitive match for strings
        if isinstance(data, str):
            return self.filter_value in data.lower()
        return self.filter_value == data
