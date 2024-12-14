import asyncio
import logging

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QScreen

from app.models.coinbase_model import CoinbaseHoldingsModel
from app.models.defi_model import DefiPositionsModel
from app.models.wallet_address_model import WalletAddressModel
from app.models.sorting_model import CustomSortFilterProxyModel
from app.helpers.utils import load_settings
from app.widgets.menu_bar import AppMenu
from app.widgets.status_label import StatusLabel
from app.widgets.table import CustomTableWidget


class CryptoDashboard(QMainWindow):
    supports_update_menu = None

    def __init__(self, window_manager):
        super().__init__()
        screen = QScreen(self)
        self.setWindowTitle("Crypto Dashboard")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.window_manager = window_manager

        # Initialize models
        self.coinbase_model = CoinbaseHoldingsModel()
        self.wallet_model = WalletAddressModel()
        self.defi_model = DefiPositionsModel()

        # Proxy Models for sorting/filtering
        self.coinbase_proxy_model = CustomSortFilterProxyModel()
        self.coinbase_proxy_model.setSourceModel(self.coinbase_model)

        self.wallet_proxy_model = CustomSortFilterProxyModel()
        self.wallet_proxy_model.setSourceModel(self.wallet_model)

        self.defi_proxy_model = CustomSortFilterProxyModel()
        self.defi_proxy_model.setSourceModel(self.defi_model)

        # Connect close_all_windows signal
        self.window_manager.close_all_windows.connect(self.close)

        # Init UI
        self.setup_ui()

        # Shared menu bar
        self.menu_bar = AppMenu(self)
        self.setMenuBar(self.menu_bar)

        # Status Label
        self.status_label = StatusLabel(parent=self)
        self.layout_with_status.addWidget(self.status_label, alignment=Qt.AlignBottom | Qt.AlignRight)

        # Connect model signals
        self.coinbase_model.data_changed.connect(self.refresh_coinbase_table)
        self.wallet_model.data_changed.connect(self.refresh_wallet_table)
        self.defi_model.data_changed.connect(self.refresh_defi_table)

        # Schedule data update task
        asyncio.create_task(self._update_data_async())

    def setup_ui(self):
        """
        Set up the user interface for the dashboard.
        """
        # Main Layout
        self.main_layout = QHBoxLayout()

        # Left Panel
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
        self.coinbase_table.setMaximumWidth(320)
        self.left_panel.addWidget(QLabel("Coinbase Holdings"))
        self.left_panel.addWidget(self.coinbase_table)

        # Wallet Table
        self.wallet_table = CustomTableWidget(self.wallet_proxy_model)
        self.wallet_table.setMaximumWidth(320)
        self.left_panel.addWidget(QLabel("Wallet Address Holdings"))
        self.left_panel.addWidget(self.wallet_table)

        self.main_layout.addLayout(self.left_panel)

        # Right Panel
        self.right_panel = QVBoxLayout()

        # DeFi Table
        self.defi_table = CustomTableWidget(self.defi_proxy_model)
        self.right_panel.addWidget(QLabel("DeFi Positions"))
        self.right_panel.addWidget(self.defi_table)

        self.main_layout.addLayout(self.right_panel)

        # Wrapper layout to include the status label
        self.layout_with_status = QVBoxLayout()
        self.layout_with_status.addLayout(self.main_layout)
        self.layout_with_status.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # Set layout to central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout_with_status)
        self.setCentralWidget(central_widget)

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
            if coinbase_data is not None:
                self.coinbase_model.update_data(coinbase_data)

            # Update Wallet Data
            self.status_label.show_message("Loading wallet balances...", 2000)
            wallet_data = await self.wallet_model.fetch_balances(eth_address)
            if wallet_data is not None:
                self.wallet_model.update_data(wallet_data)

            # Update DeFi Data
            self.status_label.show_message("Loading DeFi positions...", 2000)
            defi_data = await self.defi_model.fetch_data()
            if defi_data is not None:
                self.defi_model.update_data(defi_data)

            # Coinbase total
            coinbase_total = await self.coinbase_model.get_total()
            logging.info(f"Coinbase Total: {coinbase_total}")

            # Wallet total
            wallet_total = await self.wallet_model.get_total()
            logging.info(f"Wallet Total: {wallet_total}")

            # DeFi totals (custom logic)
            defi_totals = await self.defi_model.calculate_defi_totals()
            logging.info(f"DeFi Totals: {defi_totals}")
            defi_total_value = defi_totals.get("total_value", 0.0)
            defi_total_fees = defi_totals.get("total_fees", 0.0)

            # Aggregate totals
            total_value = coinbase_total + wallet_total + defi_total_value

            # Update UI labels
            self.total_value_label.setText(f"Current Portfolio Value: ${total_value:.2f}")
            self.total_fee_label.setText(f"Total Fees Collected: ${defi_total_fees:.2f}")

            self.status_label.show_message("UI refreshed successfully.", 2000)

        except Exception as e:
            logging.exception("Error updating dashboard data.")
            self.status_label.show_error(f"Error fetching data: {e}")

    def refresh_coinbase_table(self):
        """Refresh the Coinbase table."""
        self.coinbase_table.refresh()

    def refresh_wallet_table(self):
        """Refresh the Wallet table."""
        self.wallet_table.refresh()

    def refresh_defi_table(self):
        """Refresh the DeFi table."""
        self.defi_table.refresh()
