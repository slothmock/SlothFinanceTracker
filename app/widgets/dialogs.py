import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QMessageBox, QInputDialog, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon

from app.models.dataclasses import Card


class UpdateCashDialog(QDialog):
    cash_updated = Signal(float)

    def __init__(self, current_balance=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Cash Balance")
        self.setMinimumSize(300, 150)

        self.layout = QVBoxLayout()

        # Current balance display
        self.current_balance_label = QLabel(f"Current Cash Balance: £{current_balance:.2f}")
        self.current_balance_label.setObjectName("currentBalanceLabel")
        self.layout.addWidget(self.current_balance_label)

        # Input for new balance
        self.new_balance_input = QLineEdit()
        self.new_balance_input.setPlaceholderText("Enter new balance")
        self.new_balance_input.setObjectName("newBalanceInput")
        self.layout.addWidget(QLabel("New Cash Balance:"))
        self.layout.addWidget(self.new_balance_input)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_cash_balance)
        self.save_button.setObjectName("saveCashButton")
        self.layout.addWidget(self.save_button, alignment=Qt.AlignRight)

        self.setLayout(self.layout)

    def save_cash_balance(self):
        """
        Validate and emit the new cash balance.
        """
        try:
            new_balance = float(self.new_balance_input.text())
            if new_balance < 0:
                raise ValueError("Balance cannot be negative.")
            logging.info(f"Updated cash balance to: £{new_balance:.2f}")
            self.cash_updated.emit(new_balance)
            self.accept()
        except ValueError as e:
            self.new_balance_input.setStyleSheet("border: 1px solid red;")
            logging.error(f"Invalid input: {e}")


class ManageCardsDialog(QDialog):
    cards_updated = Signal(list)

    def __init__(self, current_cards=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Cards")
        self.setMinimumSize(500, 350)

        self.layout = QVBoxLayout()

        # Top layout with Table and Add/Remove Buttons
        top_layout = QHBoxLayout()

        # Cards Table
        self.cards_table = QTableWidget(0, 2)
        self.cards_table.setHorizontalHeaderLabels(["Card Name", "Balance"])
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cards_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cards_table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Add and Remove Buttons (with icons)
        self.buttons_layout = QVBoxLayout()
        self.add_button = QPushButton()
        self.add_button.setIcon(QIcon("app/assets/icons/plus.png"))
        self.add_button.setToolTip("Add Card")
        self.add_button.clicked.connect(self.add_card)

        self.remove_button = QPushButton()
        self.remove_button.setIcon(QIcon("app/assets/icons/minus.png")) 
        self.remove_button.setToolTip("Remove Selected Card")
        self.remove_button.clicked.connect(self.remove_selected_card)

        # Add Buttons to a vertical layout
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignTop)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()

        # Add table and button layout to the top layout
        top_layout.addWidget(self.cards_table)
        top_layout.addLayout(button_layout)

        # Add the top layout to the main layout
        self.layout.addLayout(top_layout)

        # Accept/Cancel Buttons at the bottom
        action_buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.cancel_button)
        action_buttons_layout.addWidget(self.accept_button)

        self.layout.addLayout(action_buttons_layout)
        self.setLayout(self.layout)

        # Populate initial cards
        if current_cards:
            for card in current_cards:
                self._add_card_to_table(card["name"], card["balance"])

    def add_card(self):
        """
        Add a new card to the table.
        """
        name, name_ok = QInputDialog.getText(self, "Add Card", "Enter card name:")

        balance, balance_ok = QInputDialog.getDouble(self, "Add Card", "Enter initial balance:", decimals=2)
        if name_ok and balance_ok and name.strip():
            self._add_card_to_table(name.strip(), balance)

    def _add_card_to_table(self, name, balance):
        """
        Add a card row to the table.
        """
        row = self.cards_table.rowCount()
        self.cards_table.insertRow(row)
        self.cards_table.setItem(row, 0, QTableWidgetItem(name))
        self.cards_table.setItem(row, 1, QTableWidgetItem(f"£{balance:.2f}"))

    def remove_selected_card(self):
        """
        Remove the selected card from the table.
        """
        selected_items = self.cards_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            self.cards_table.removeRow(selected_row)

    def accept(self):
        """
        Emit updated card data and close the dialog.
        """
        cards = []
        for row in range(self.cards_table.rowCount()):
            name_item = self.cards_table.item(row, 0)
            balance_item = self.cards_table.item(row, 1)
            if name_item and balance_item:
                try:
                    name = name_item.text()
                    balance = float(balance_item.text().replace("£", ""))
                    cards.append(Card(name=name, balance=balance))
                except ValueError:
                    continue  # Skip invalid rows
        self.cards_updated.emit(cards)
        super().accept()


class AddTransactionDialog(QDialog):
    def __init__(self, prefill_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Transaction")
        self.setMinimumSize(400, 300)

        # Layout
        self.layout = QVBoxLayout()

        # Inputs
        self.inputs = {}
        fields = ["Source", "Date", "Name", "Description", "Amount", "Type"]
        for field in fields:
            label = QLabel(field)
            input_field = QLineEdit()

            # Date-specific configuration
            if field == "Date":
                input_field = QDateEdit()
                input_field.setDate(QDate.currentDate())
                input_field.setCalendarPopup(True)

            self.layout.addWidget(label)
            self.layout.addWidget(input_field)
            self.inputs[field] = input_field

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_transaction)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addWidget(self.save_button)
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

        # Prefill data if provided
        if prefill_data:
            self.prefill_data(prefill_data)

    def prefill_data(self, data):
        """
        Prefill the dialog with existing data.
        """
        for key, value in data.items():
            if key == "Date":
                # Handle date-specific prefilling
                self.inputs[key].setDate(QDate.fromString(value, "dd-MM-yyyy"))
            elif key in self.inputs:
                # Handle other fields
                self.inputs[key].setText(str(value).replace("£", ""))

    def save_transaction(self):
        """
        Validate and return the transaction data.
        """
        transaction = {}
        try:
            for key, input_field in self.inputs.items():
                if key == "Date":
                    # Convert QDateEdit value to string in the correct format
                    transaction[key] = input_field.date().toString("dd-MM-yyyy")
                elif key == "Amount":
                    # Validate and convert amount to float
                    transaction[key] = float(input_field.text())
                else:
                    # Handle other fields as strings
                    transaction[key] = input_field.text()

            self.accept()  # Close dialog with QDialog.Accepted
            self.transaction_data = transaction  # Store transaction for retrieval
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Error in input data: {e}")

    def get_transaction(self):
        """
        Return the transaction data after the dialog is accepted.
        """
        return getattr(self, "transaction_data", None)