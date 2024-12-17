import logging
import asyncio
import csv

from PySide6.QtCore import Qt, QDate, QSize, QEvent
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QLineEdit, QSpacerItem, QMessageBox, QComboBox, QSizePolicy
)

from app.models.dataclasses import DefiPosition
from app.models.defi_model import DefiPositionsModel
from app.helpers.strings import DEFI_POS_FILE
from app.widgets.menu_bar import AppMenu
from app.widgets.status_label import StatusLabel
from app.widgets.table import CustomTableWidget


class PositionTracker(QMainWindow):
    supports_update_menu = None

    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("DeFi Positions Dashboard")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        self.window_manager = window_manager
        self.defi_model = DefiPositionsModel()

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
        # Main layout
        self.main_layout = QVBoxLayout()

        # Filter layout for "Pool"
        self.filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Filter by Pool:")
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.addItem("All")
        self.filter_dropdown.currentTextChanged.connect(self.apply_filter)
        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_dropdown)
        self.main_layout.addLayout(self.filter_layout)

        # Table view
        self.positions_table = CustomTableWidget(self.defi_model)
        self.positions_table.setSortingEnabled(True)
        self.main_layout.addWidget(QLabel("DeFi Position History"))
        self.main_layout.addWidget(self.positions_table)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.add_position_button = QPushButton("Add/Edit Position")
        self.add_position_button.clicked.connect(self.add_position)
        self.buttons_layout.addWidget(self.add_position_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        self.buttons_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(self.buttons_layout)

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
        Fetch data asynchronously and update the model.
        """
        try:
            self.status_label.show_message("Fetching data...", 2000)

            # Fetch data asynchronously
            data = await self.defi_model.fetch_data()
            if data is not None:
                self.defi_model.update_data(data)

            # Update filter dropdown
            self.update_filter_dropdown()

            self.status_label.show_message("DeFi positions updated successfully.", 2000)
        except Exception as e:
            logging.exception("Error updating positions data.")
            self.status_label.show_message(f"Error: {e}", error=True)

    def refresh(self):
        """
        Refresh the data displayed in the dashboard.
        """
        asyncio.create_task(self._update_data_async())

    def update_filter_dropdown(self):
        """
        Populate the filter dropdown with unique pool names.
        """
        pools = {row.Pool for row in self.defi_model._data}
        self.filter_dropdown.clear()
        self.filter_dropdown.addItem("All")
        self.filter_dropdown.addItems(sorted(pools))

    def apply_filter(self, pool_name):
        """
        Apply the selected filter to the positions table.
        """
        self.positions_table.set_filter("Pool", pool_name)

    def add_position(self):
        """
        Open a dialog to add a new position and refresh the data.
        """
        row_index = self.positions_table.get_current_row()
        if row_index != -1:
            data = self.defi_model._data[row_index]    
            dialog = PositionDialog(filepath=DEFI_POS_FILE, prefill_data=data)
        else:
            dialog = PositionDialog(filepath=DEFI_POS_FILE, prefill_data=None)    
        if dialog.exec():
            asyncio.create_task(self._update_data_async())

class PositionDialog(QDialog):
    def __init__(self, filepath=DEFI_POS_FILE, prefill_data=None):
        super().__init__()
        self.setWindowTitle("Add/Update Position")
        self.filepath = filepath

        # Main Layout
        self.layout = QVBoxLayout()

        # Date Input with Calendar
        self.date_label = QLabel("Date")
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.layout.addWidget(self.date_label)
        self.layout.addWidget(self.date_input)

        # Other Inputs
        self.inputs = {}
        fields = ["Source", "Pool", "T1 Amount", "T2 Amount", "T1 Value", "T2 Value", "Fees"]
        for field in fields:
            label = QLabel(field)
            input_field = QLineEdit()
            self.layout.addWidget(label)
            self.layout.addWidget(input_field)
            self.inputs[field] = input_field

        spacer = QSpacerItem(0, 20)
        self.layout.addSpacerItem(spacer)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Position")
        self.save_button.clicked.connect(self.save_position)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addWidget(self.save_button)
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

        # Prefill data if provided
        if prefill_data:
            self.prefill_data(prefill_data)

    def prefill_data(self, data: DefiPosition):
        """
        Prefill the dialog with existing data.
        """
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            print(f"{field} - {value}")
            if field == "Date":
                self.date_input.setDate(QDate.fromString(data.Date, "dd-MM-YYYY"))
            elif field == "Total_Value":
                pass
            else:
                self.inputs[field.replace("_", " ")].setText(str(value).replace("$", ""))
            

    def save_position(self):
        """
        Save the position to the CSV file.
        """
        try:
            # Gather data
            data = {
                "Date": self.date_input.date().toString("dd-MM-yyyy"),
                **{key: self.inputs[key].text() for key in self.inputs}
            }

            # Append to CSV
            with open(self.filepath, "a", newline="\n") as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if file.tell() == 0:  # Write header only if the file is empty
                    writer.writeheader()
                writer.writerow(data)

            self.accept()
        except Exception as e:
            logging.exception(f"Error saving position: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save position: {e}")
