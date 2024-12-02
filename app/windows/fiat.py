import asyncio
import csv
from datetime import datetime
import logging
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QTabWidget, QFileDialog, QWidget, QMessageBox
)
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtCore import Qt, QSize
import aiofiles
from app.widgets.menu_bar import AppMenu
from app.widgets.dialogs import AddTransactionDialog


class FiatDashboard(QMainWindow):
    supports_update_menu = "expense_overview"
    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("Fiat Dashboard")
        self.setMinimumSize(QSize(900, 700))

        # Connect close_all_windows signal
        window_manager.close_all_windows.connect(self.close)

        # Initialize data
        self.transactions = []
        self.total_cash = 0.0
        self.total_cards = 0.0
        self.transactions_csv_file = "user_data/transactions.csv"  # Default CSV file for saving/loading

        # Init UI
        self.setup_ui()

        # Shared menu bar
        self.setMenuBar(AppMenu(self))

        # Load transactions and update running total
        asyncio.create_task(self.load_transactions())

    def setup_ui(self):
        """
        Initialize the user interface.
        """
        self.main_layout = QVBoxLayout()

        # Running Total Label
        self.running_total_label = QLabel("Total: £0.00")
        self.running_total_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.running_total_label.setAlignment(Qt.AlignLeft)
        self.main_layout.addWidget(self.running_total_label)

        # Tabs
        self.tab_widget = QTabWidget()

        # Transactions Tab
        self.transactions_tab = QWidget()
        self.transactions_layout = QVBoxLayout()
        self.transactions_tab.setLayout(self.transactions_layout)

        # Transactions Table
        self.transactions_table = QTableWidget(0, 3)
        self.transactions_table.setHorizontalHeaderLabels(["Date", "Description", "Amount"])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_layout.addWidget(self.transactions_table)

        # Transactions Buttons
        self.transactions_buttons = QHBoxLayout()
        add_income_button = QPushButton("Add Income")
        add_income_button.clicked.connect(self.open_add_income_dialog)
        self.transactions_buttons.addWidget(add_income_button)

        add_expense_button = QPushButton("Add Expense")
        add_expense_button.clicked.connect(self.open_add_expense_dialog)
        self.transactions_buttons.addWidget(add_expense_button)

        save_csv_button = QPushButton("Save to CSV")
        save_csv_button.clicked.connect(self.save_to_csv)
        self.transactions_buttons.addWidget(save_csv_button)

        self.transactions_layout.addLayout(self.transactions_buttons)
        self.tab_widget.addTab(self.transactions_tab, "Transactions")

        # Chart Tab
        self.chart_tab = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_tab.setLayout(self.chart_layout)

        # Pie Chart
        self.chart = QChart()
        self.chart.setTitle("Expenses and Income Breakdown")
        self.chart_view = QChartView(self.chart)
        self.chart_layout.addWidget(self.chart_view)

        self.tab_widget.addTab(self.chart_tab, "Charts")
        self.main_layout.addWidget(self.tab_widget)

        # Central Widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    async def load_transactions(self):
        """
        Load transactions from the default CSV file asynchronously.
        """
        try:
            async with aiofiles.open(self.transactions_csv_file, mode="r") as file:
                reader = csv.DictReader(await file.read())
                for row in reader:
                    self.transactions.append({
                        "date": row["Date"],
                        "description": row["Description"],
                        "amount": float(row["Amount"]),
                    })
                self.refresh_transactions_table()
                asyncio.create_task(self.update_running_total())
                self.update_chart()
        except FileNotFoundError:
            logging.warning(f"No existing CSV file found at {self.transactions_csv_file}. Starting fresh.")
        except Exception as e:
            logging.exception(f"Error loading transactions from CSV: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load transactions: {e}")

    async def update_running_total(self):
        """
        Calculate and update the running total asynchronously.
        """
        total = self.total_cash + self.total_cards + sum([t["amount"] for t in self.transactions])
        self.running_total_label.setText(f"Total: £{total:.2f}")

    def refresh_transactions_table(self):
        """
        Refresh the transactions table with current data.
        """
        self.transactions_table.setRowCount(0)
        for transaction in self.transactions:
            row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row)
            self.transactions_table.setItem(row, 0, QTableWidgetItem(transaction["date"]))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(transaction["description"]))
            amount_item = QTableWidgetItem(f"£{transaction['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight)
            self.transactions_table.setItem(row, 2, amount_item)

    def update_chart(self):
        """
        Update the pie chart with the latest transactions.
        """
        income = sum(t["amount"] for t in self.transactions if t["amount"] > 0)
        expenses = abs(sum(t["amount"] for t in self.transactions if t["amount"] < 0))

        series = QPieSeries()
        if income > 0:
            series.append("Income", income)
        if expenses > 0:
            series.append("Expenses", expenses)

        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

    def open_add_income_dialog(self):
        """
        Open a dialog to add income.
        """
        dialog = AddTransactionDialog(transaction_type="Income", parent=self)
        if dialog.exec():
            transaction = dialog.get_transaction()
            self.transactions.append(transaction)
            self.refresh_transactions_table()
            asyncio.create_task(self.update_running_total())
            self.update_chart()

    def open_add_expense_dialog(self):
        """
        Open a dialog to add an expense.
        """
        dialog = AddTransactionDialog(transaction_type="Expense", parent=self)
        if dialog.exec():
            transaction = dialog.get_transaction()
            self.transactions.append(transaction)
            self.refresh_transactions_table()
            asyncio.create_task(self.update_running_total())
            self.update_chart()

    def save_to_csv(self):
        """
        Save transactions to a CSV file.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transactions", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            asyncio.create_task(self._save_to_csv(file_path))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving to CSV: {e}")

    async def _save_to_csv(self, file_path):
        """
        Asynchronous helper to save transactions to a CSV file.
        """
        try:
            async with aiofiles.open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Description", "Amount"])
                for transaction in self.transactions:
                    writer.writerow([transaction["date"], transaction["description"], transaction["amount"]])
            QMessageBox.information(self, "Success", "Transactions saved to CSV.")
        except Exception as e:
            logging.exception(f"Error saving to CSV: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save CSV: {e}")