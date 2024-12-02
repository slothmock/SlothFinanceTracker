import asyncio
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

from app.helpers.models import CoinbaseHoldingsModel, DefiPositionsModel, WalletAddressModel
from app.helpers.proxy_model import CustomProxyModel
from app.helpers.utils import load_settings
from app.widgets.menu_bar import AppMenu
from app.widgets.status_label import StatusLabel
from app.widgets.table import CustomTableWidget


from PySide6.QtCore import QEvent

class CryptoDashboard(QMainWindow):
    supports_update_menu = True

    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("Crypto Dashboard")
        self.setMinimumSize(QSize(1280, 720))

        self.window_manager = window_manager

        # Models
        self.coinbase_model = CoinbaseHoldingsModel()
        self.wallet_model = WalletAddressModel()
        self.defi_model = DefiPositionsModel()

        # Proxy Models for sorting and filtering
        self.coinbase_proxy_model = CustomProxyModel()
        self.coinbase_proxy_model.setSourceModel(self.coinbase_model)

        self.wallet_proxy_model = CustomProxyModel()
        self.wallet_proxy_model.setSourceModel(self.wallet_model)

        self.defi_proxy_model = CustomProxyModel()
        self.defi_proxy_model.setSourceModel(self.defi_model)

        # Connect close_all_windows signal
        self.window_manager.close_all_windows.connect(self.close)

        # Shared menu bar
        self.menu_bar = AppMenu(self)
        self.setMenuBar(self.menu_bar)

        # Init UI
        self.setup_ui()

        # Add StatusLabel
        self.status_label = StatusLabel(parent=self)
        self.layout_with_status.addWidget(self.status_label, alignment=Qt.AlignBottom | Qt.AlignRight)

        # Schedule data update task
        asyncio.create_task(self._update_data_async())

    def setup_ui(self):
        """
        Set up the user interface for the dashboard.
        """
        # Main Layout (Horizontal: Left and Right Panels)
        self.main_layout = QHBoxLayout()

        # Left Panel: Coinbase and Wallet Address Tables
        self.left_panel = QVBoxLayout()

        # Total Portfolio Value Label
        self.total_value_label = QLabel("Total Portfolio Value: Calculating...")
        self.total_value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.left_panel.addWidget(self.total_value_label)

        # Total Fee Revenue Label
        self.total_fee_label = QLabel("Total Fee Revenue: Calculating...")
        self.total_fee_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.left_panel.addWidget(self.total_fee_label)

        # Coinbase Table
        self.coinbase_table = CustomTableWidget(self.coinbase_proxy_model)
        self.coinbase_table.setFixedWidth(300)
        self.left_panel.addWidget(QLabel("Coinbase Holdings"))
        self.left_panel.addWidget(self.coinbase_table)

        # Wallet Table
        self.wallet_table = CustomTableWidget(self.wallet_proxy_model)
        self.wallet_table.setFixedWidth(300)
        self.left_panel.addWidget(QLabel("Wallet Address Holdings"))
        self.left_panel.addWidget(self.wallet_table)

        self.main_layout.addLayout(self.left_panel)

        # Right Panel: DeFi Table
        self.right_panel = QVBoxLayout()

        self.defi_table = CustomTableWidget(self.defi_proxy_model)
        self.right_panel.addWidget(QLabel("DeFi Positions"))
        self.right_panel.addWidget(self.defi_table)

        self.main_layout.addLayout(self.right_panel)

        # Wrapper layout to include the status label
        self.layout_with_status = QVBoxLayout()
        self.layout_with_status.addLayout(self.main_layout)

        # Spacer for pushing status label to the bottom
        self.layout_with_status.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # Set the layout to the central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout_with_status)
        self.setCentralWidget(central_widget)

        # Update the menu bar dynamically
        self.menu_bar.dynamic_update_menu()

    def event(self, event):
        """
        Overriding event to trigger dynamic menu updates on window activation.
        """
        if event.type() == QEvent.WindowActivate:
            self.menu_bar.dynamic_update_menu()
        return super().event(event)

    async def _update_data_async(self):
        """
        Fetch data asynchronously and update all models.
        """
        try:
            self.status_label.show_message("Loading data...", 2000)

            # Load settings
            settings = await load_settings()
            eth_address = settings.get("eth_address", "")

            # Update Coinbase Data
            self.status_label.show_message("Loading Coinbase holdings...", 2000)
            coinbase_data = await self.coinbase_model.get_cb_holdings()
            self.coinbase_model.update_data(coinbase_data)

            # Update Wallet Data
            self.status_label.show_message("Loading wallet balances...", 2000)
            wallet_data = await self.wallet_model.fetch_balances(eth_address)
            self.wallet_model.update_data(wallet_data)

            # Update DeFi Data
            self.status_label.show_message("Loading DeFi positions...", 2000)
            defi_data = await self.defi_model.fetch_data()
            self.defi_model.update_data(defi_data)

            # Calculate totals
            self.status_label.show_message("Calculating totals...", 2000)
            total_value = (
                await self.coinbase_model.calculate_total()
                + await self.wallet_model.calculate_total()
                + await self.defi_model.calculate_total()
            )

            # Calculate total fee revenue
            fee_revenue = await self.defi_model.calculate_fee_total()

            # Update labels
            self.total_value_label.setText(f"Current Portfolio Value: ${total_value:.2f}")
            self.total_fee_label.setText(f"Total Fees Collected: ${fee_revenue:.2f}")

            self.status_label.show_message("UI refreshed successfully.", 2000)

        except Exception as e:
            logging.exception("Error updating overview data.")
            self.total_value_label.setText(f"Error fetching data: {e}")

    def refresh(self):
        """
        Refresh the data displayed in the dashboard.
        """
        asyncio.create_task(self._update_data_async())