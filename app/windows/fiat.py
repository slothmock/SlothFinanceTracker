import asyncio
import logging

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QHeaderView,
)
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtCore import Qt, QSize, QEvent

from app.widgets.menu_bar import AppMenu
from app.widgets.dialogs import AddTransactionDialog, ManageCardsDialog, UpdateCashDialog
from app.models.fiat_model import FiatModel
from app.models.sorting_model import CustomSortFilterProxyModel
from app.widgets.status_label import StatusLabel
from app.widgets.table import CustomTableWidget


class FiatDashboard(QMainWindow):
    supports_update_menu = "fiat_overview"

    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("Fiat Dashboard")
        self.setMinimumSize(QSize(900, 700))

        # Initialize model and proxy
        self.data_model = FiatModel()
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.data_model)

        # Connect close_all_windows signal
        window_manager.close_all_windows.connect(self.close)

        # Init UI
        self.setup_ui()

        # Shared menu bar
        self.menu_bar = AppMenu(self)
        self.setMenuBar(self.menu_bar)

        # Connect model signals to update UI
        self.data_model.cash_updated.connect(self.refresh_cash_label)
        self.data_model.cards_updated.connect(self.refresh_cards_label)
        self.data_model.data_changed.connect(self.refresh_ui)

        # Load transactions, cash, and cards from the JSON file
        asyncio.create_task(self.data_model.load_from_file())

    def event(self, event):
        """
        Overriding event to trigger dynamic menu updates on window activation.
        """
        if event.type() == QEvent.WindowActivate:
            self.menu_bar.dynamic_update_menu()
        return super().event(event)

    def setup_ui(self):
        self.main_layout = QVBoxLayout()

        # Balances Display
        balances_layout = QVBoxLayout()
        self.total_label = QLabel("Total: £0.00")
        self.cash_label = QLabel("Cash: £0.00")
        self.cards_label = QLabel("Cards: £0.00")

        for label in [self.cash_label, self.cards_label, self.total_label]:
            label.setStyleSheet("font-size: 18px; font-weight: bold;")
            balances_layout.addWidget(label)

        self.main_layout.addLayout(balances_layout)

        # Transactions Section
        transactions_layout = QVBoxLayout()

        # Add/Edit Button (top-right of the table)
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Push button to the right
        self.add_edit_button = QPushButton("Add/Edit Transaction")
        self.add_edit_button.clicked.connect(self.open_add_edit_transaction_dialog)
        button_layout.addWidget(self.add_edit_button)
        transactions_layout.addLayout(button_layout)

        # Transactions Table
        self.transactions_table = CustomTableWidget(self.proxy_model)
        self.transactions_table.setAlternatingRowColors(True)
        self.transactions_table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        transactions_layout.addWidget(self.transactions_table)

        # Status Label (bottom-right of the table)
        status_layout = QHBoxLayout()
        status_layout.addStretch()  # Push label to the right
        self.status_label = StatusLabel()
        status_layout.addWidget(self.status_label)
        transactions_layout.addLayout(status_layout)

        # Wrap Transactions Section into a Tab
        self.transactions_tab = QWidget()
        self.transactions_tab.setLayout(transactions_layout)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.transactions_tab, "Transactions")

        # Chart Tab
        self.chart_tab = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart = QChart()
        self.chart.setTitle("Expenses and Income Breakdown")
        self.chart_view = QChartView(self.chart)
        self.chart_layout.addWidget(self.chart_view)
        self.chart_tab.setLayout(self.chart_layout)
        self.tab_widget.addTab(self.chart_tab, "Charts")

        self.main_layout.addWidget(self.tab_widget)

        # Central Widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def refresh_cash_label(self, new_cash):
        self.cash_label.setText(f"Cash: £{new_cash:.2f}")
        self.refresh_total_label()

    def refresh_cards_label(self, new_cards_total):
        self.cards_label.setText(f"Cards: £{new_cards_total:.2f}")
        self.refresh_total_label()

    def refresh_total_label(self):
        total = self.data_model.total_funds
        self.total_label.setText(f"Total: £{total:.2f}")

    def refresh_ui(self):
        """
        Refresh the UI, including the table, chart, and totals.
        """
        self.transactions_table.refresh()
        self.refresh_chart()

    def refresh_chart(self):
        """
        Update the pie chart with the latest transactions.
        """
        income, expenses = self.data_model.calculate_income_expenses()

        series = QPieSeries()
        if income > 0:
            series.append("Income", income)
        if expenses > 0:
            series.append("Expenses", abs(expenses))

        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

    def open_add_edit_transaction_dialog(self):
        """
        Open the Add/Edit Transaction dialog, prefill data if editing an existing transaction,
        and update or add a transaction based on user input.
        """
        selected_row = self.transactions_table.get_current_row()
        logging.debug(f"Selected row for editing: {selected_row}")

        # Fetch prefill data if editing an existing transaction
        prefill_data = self.get_transaction_data(selected_row) if selected_row >= 0 else None
        logging.debug(f"Prefill data for dialog: {prefill_data}")

        # Open the dialog with prefill data
        dialog = AddTransactionDialog(prefill_data=prefill_data, parent=self)
        if dialog.exec():
            transaction = dialog.get_transaction()
            logging.debug(f"Transaction data from dialog: {transaction}")

            if selected_row >= 0:
                self.data_model.update_transaction(selected_row, transaction)
            else:
                self.add_transaction(transaction)

            # Save changes to JSON asynchronously
            asyncio.create_task(self.data_model.save_to_file())

            # Refresh the UI after modification
            self.refresh_ui()

    def open_update_cash_dialog(self):
        """
        Open the Update Cash dialog and update the cash balance.
        """
        dialog = UpdateCashDialog(current_balance=self.data_model.total_cash, parent=self)
        dialog.cash_updated.connect(self.data_model.update_cash)
        dialog.exec()

    def open_manage_cards_dialog(self):
        """
        Open the Manage Cards dialog and update card balances.
        """
        dialog = ManageCardsDialog(current_cards=self.data_model.cards, parent=self)
        dialog.cards_updated.connect(self.data_model.update_cards)
        dialog.exec()

    def get_transaction_data(self, row):
        """
        Retrieve transaction data for a specific row.
        
        Args:
            row (int): The row index to retrieve data from.
        
        Returns:
            dict: A dictionary of transaction data for the given row.
        """
        if row < 0 or row >= self.data_model.rowCount():
            logging.warning(f"Row {row} is out of range. Cannot fetch transaction data.")
            return None

        return {
            header: self.data_model.data(
                self.data_model.index(row, col), Qt.DisplayRole
            )
            for col, header in enumerate(self.data_model.headers)
        }

    def update_transaction(self, row, transaction):
        """
        Update an existing transaction in the model.

        Args:
            row (int): The index of the row to update.
            transaction (dict): The new transaction data.
        """
        try:
            self.data_model.update_transaction(row, transaction)
            logging.info(f"Transaction at row {row} updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update transaction at row {row}: {e}")

    def add_transaction(self, transaction):
        """
        Add a new transaction to the model.

        Args:
            transaction (dict): The transaction data to add.
        """
        try:
            self.data_model.add_transaction(transaction)
            logging.info("New transaction added successfully.")
        except Exception as e:
            logging.error(f"Failed to add new transaction: {e}")
