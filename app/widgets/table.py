from PySide6.QtWidgets import QTableView, QHeaderView
from PySide6.QtCore import Qt, QSortFilterProxyModel

from app.helpers.models import CustomSortFilterProxyModel


class CustomTableWidget(QTableView):
    """
    A custom table widget for advanced functionality, including sorting and filtering.
    """
    def __init__(self, model=None, parent=None):
        super().__init__(parent)

        self.last_sorted_column = 0  # Track the last sorted column
        self.sort_order = Qt.SortOrder.DescendingOrder  # Track the last sort order, default to descending

        # Initialize proxy model for filtering and sorting
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterKeyColumn(-1)  # Default to no filtering
        if model:
            self.set_model(model)

        # Set up the table view
        self.setModel(self.proxy_model)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Default sorting
        self.sortByColumn(0, self.sort_order)

        # Signal to track column sorting
        self.horizontalHeader().sectionClicked.connect(self.on_section_clicked)

    def get_current_row(self):
        """
        Get the currently selected row index.
        
        Returns:
            int: The index of the currently selected row, or -1 if no row is selected.
        """
        current_index = self.currentIndex()
        return current_index.row() if current_index.isValid() else -1

    def set_model(self, model):
        """
        Set the model for the table widget and refresh the view.
        
        Args:
            model (QAbstractItemModel): The model to set for the table.
        """
        if model is not None:
            self.proxy_model.setSourceModel(model)
            self.refresh()
        else:
            raise ValueError("Cannot set a null model.")

    def refresh(self):
        """
        Refresh the table view when data changes.
        """
        if self.model():
            self.model().layoutChanged.emit()

    def on_section_clicked(self, index):
        """
        Handle column header clicks for sorting.
        
        Args:
            index (int): The column index that was clicked.
        """
        if self.last_sorted_column == index:
            # Toggle the sort order for the same column
            self.sort_order = (
                Qt.SortOrder.DescendingOrder
                if self.sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            # Reset to ascending order for a new column
            self.last_sorted_column = index
            self.sort_order = Qt.SortOrder.AscendingOrder

        # Apply sorting
        self.sortByColumn(index, self.sort_order)

    def reset_sorting(self, column=0, order=Qt.SortOrder.DescendingOrder):
        """
        Reset sorting to a specific column and order.
        
        Args:
            column (int): The column index to sort by. Defaults to 0.
            order (Qt.SortOrder): The sorting order. Defaults to ascending.
        """
        self.last_sorted_column = column
        self.sort_order = order
        self.sortByColumn(column, order)

    def set_filter(self, column_name, filter_value):
        """
        Set a filter for the table using the proxy model.
        
        Args:
            column_name (str): The name of the column to filter.
            filter_value (str): The value to filter for.
        """
        model = self.proxy_model.sourceModel()
        if model:
            try:
                column_index = model.headers.index(column_name)  # Match column name to index
                if filter_value in ["", "All"]:  # Clear filter if "All" or empty
                    self.proxy_model.setFilterKeyColumn(-1)
                    self.proxy_model.setFilterRegularExpression("")
                    self.reset_sorting()
                else:
                    self.proxy_model.setFilterKeyColumn(column_index)
                    self.proxy_model.setFilterRegularExpression(filter_value)
            except ValueError:
                raise ValueError(f"Column '{column_name}' does not exist in the model headers.")
