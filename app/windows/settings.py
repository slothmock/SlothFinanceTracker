import asyncio
import logging

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
    QTabWidget, QWidget, QInputDialog, QHeaderView
)
from PySide6.QtCore import QEvent, QSize, Qt

from app.helpers.utils import load_settings, save_settings, load_credentials, save_credentials
from app.widgets.menu_bar import AppMenu
from app.widgets.status_label import StatusLabel


class SettingsDashboard(QMainWindow):
    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setMinimumSize(QSize(400, 200))

        # Connect close_all_windows signal
        window_manager.close_all_windows.connect(self.close)

        # Shared menu bar
        self.setMenuBar(AppMenu(self))

        # Initialize instance variables
        self.settings = {}
        self.credentials = {}

        # UI Setup
        self.setup_ui()

        # Add StatusLabel
        self.status_label = StatusLabel()
        self.main_layout.addWidget(self.status_label, alignment=Qt.AlignBottom | Qt.AlignRight)

    def showEvent(self, event: QEvent):
        """
        Trigger asynchronous data loading when the window is shown.
        """
        super().showEvent(event)
        asyncio.create_task(self.load_data())

    def setup_ui(self):
        """
        Configure the UI components for the settings dashboard.
        """
        # Main Layout
        self.main_layout = QVBoxLayout()

        # Tab Widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # General Settings Tab
        self.general_settings_tab = self.create_general_settings_tab()
        self.tabs.addTab(self.general_settings_tab, "General Settings")

        # API Credentials Tab
        self.api_credentials_tab = self.create_api_credentials_tab()
        self.tabs.addTab(self.api_credentials_tab, "API Credentials")

        # Watchlist Tab
        self.watchlist_tab = self.create_watchlist_tab()
        self.tabs.addTab(self.watchlist_tab, "Watchlist")

        # Save Button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(lambda: asyncio.create_task(self.save_settings()))
        self.main_layout.addWidget(self.save_button)

        # Central widget and layout assignment
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.adjustSize()

    async def load_data(self):
        """
        Asynchronously load settings and credentials.
        """
        try:
            self.status_label.show_message("Loading settings...", 2000)

            self.settings = await load_settings()
            self.credentials = await load_credentials()

            self.eth_wallet_address_input.setText(self.settings.get("eth_address", ""))
            self.sol_wallet_address_input.setText(self.settings.get("sol_address", ""))
            self.api_key_input.setText(self.credentials.get("coinbase_api_key", ""))
            self.api_secret_input.setText(self.credentials.get("coinbase_api_secret", ""))

            self.populate_watchlist_table()
            self.status_label.show_message("Settings loaded successfully.", 2000)
        except Exception as e:
            logging.exception(f"Error loading settings or credentials: {e}")
            self.status_label.show_message("Failed to load settings.", error=True)

    def create_general_settings_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setVerticalSpacing(5)
        layout.setHorizontalSpacing(10)

        # General Settings Widgets
        eth_wallet_label = QLabel("ETH Wallet Address:")
        self.eth_wallet_address_input = QLineEdit()

        sol_wallet_label = QLabel("SOL Wallet Address:")
        self.sol_wallet_address_input = QLineEdit()

        # Add to Grid
        layout.addWidget(eth_wallet_label, 0, 0)
        layout.addWidget(self.eth_wallet_address_input, 0, 1)
        layout.addWidget(sol_wallet_label, 1, 0)
        layout.addWidget(self.sol_wallet_address_input, 1, 1)

        tab.setLayout(layout)
        return tab

    def create_api_credentials_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setVerticalSpacing(5)
        layout.setHorizontalSpacing(10)

        # API Credentials Widgets
        api_key_label = QLabel("Coinbase API Key:")
        self.api_key_input = QLineEdit()

        api_secret_label = QLabel("Coinbase API Secret:")
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)

        # Add to Grid
        layout.addWidget(api_key_label, 0, 0)
        layout.addWidget(self.api_key_input, 0, 1)
        layout.addWidget(api_secret_label, 1, 0)
        layout.addWidget(self.api_secret_input, 1, 1)

        tab.setLayout(layout)
        return tab

    def create_watchlist_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Watchlist Table
        self.watchlist_table = QTableWidget(0, 2)
        self.watchlist_table.setHorizontalHeaderLabels(["Token Name", "Contract Address"])
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("Watchlist:"))
        layout.addWidget(self.watchlist_table)

        # Add and Remove Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Token")
        remove_button = QPushButton("Remove Selected")
        add_button.clicked.connect(self.add_to_watchlist)
        remove_button.clicked.connect(self.remove_from_watchlist)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)

        tab.setLayout(layout)
        return tab

    def populate_watchlist_table(self):
        """
        Populate the watchlist table with data from settings.json.
        """
        self.watchlist_table.setRowCount(0)
        for token in self.settings.get("watchlist", []):
            row = self.watchlist_table.rowCount()
            self.watchlist_table.insertRow(row)
            self.watchlist_table.setItem(row, 0, QTableWidgetItem(token["name"]))
            self.watchlist_table.setItem(row, 1, QTableWidgetItem(token["contract_address"]))

    def add_to_watchlist(self):
        """
        Add a new token to the watchlist.
        """
        name, name_ok = QInputDialog.getText(self, "Add Token", "Enter token name:")
        address, address_ok = QInputDialog.getText(self, "Add Token", "Enter contract address:")
        if name_ok and address_ok and name.strip() and address.strip():
            row = self.watchlist_table.rowCount()
            self.watchlist_table.insertRow(row)
            self.watchlist_table.setItem(row, 0, QTableWidgetItem(name.strip()))
            self.watchlist_table.setItem(row, 1, QTableWidgetItem(address.strip()))

    def remove_from_watchlist(self):
        """
        Remove the selected token(s) from the watchlist.
        """
        for row in sorted({item.row() for item in self.watchlist_table.selectedItems()}, reverse=True):
            self.watchlist_table.removeRow(row)

    async def save_settings(self):
        """
        Save all settings, including the watchlist, asynchronously.
        """
        try:
            self.status_label.show_message("Saving settings...", 2000)

            self.settings.update({
                "eth_address": self.eth_wallet_address_input.text(),
                "sol_address": self.sol_wallet_address_input.text(),
                "watchlist": [
                    {
                        "name": self.watchlist_table.item(row, 0).text(),
                        "contract_address": self.watchlist_table.item(row, 1).text()
                    }
                    for row in range(self.watchlist_table.rowCount())
                ],
            })
            await save_settings(self.settings)

            self.credentials.update({
                "coinbase_api_key": self.api_key_input.text(),
                "coinbase_api_secret": self.api_secret_input.text(),
            })
            await save_credentials(self.credentials)

            self.status_label.show_message("Settings saved successfully.", 2000)
            logging.info("Settings saved successfully.")
        except Exception as e:
            logging.exception(f"Error saving settings: {e}")
            self.status_label.show_message("Failed to save settings.", error=True)
