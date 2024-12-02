from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QInputDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt
import logging


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
        self.setMinimumSize(400, 300)

        self.layout = QVBoxLayout()

        # Cards Table
        self.cards_table = QTableWidget(0, 2)
        self.cards_table.setHorizontalHeaderLabels(["Card Name", "Balance"])
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.cards_table)

        # Add and Remove Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Card")
        self.add_button.clicked.connect(self.add_card)
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_card)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        self.layout.addLayout(button_layout)

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
        if name_ok and balance_ok:
            self._add_card_to_table(name, balance)

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
        Remove selected cards from the table.
        """
        selected_rows = {item.row() for item in self.cards_table.selectedItems()}
        for row in sorted(selected_rows, reverse=True):
            self.cards_table.removeRow(row)

    def accept(self):
        """
        Emit updated card data and close the dialog.
        """
        cards = []
        for row in range(self.cards_table.rowCount()):
            name = self.cards_table.item(row, 0).text()
            balance = float(self.cards_table.item(row, 1).text().replace("£", ""))
            cards.append({"name": name, "balance": balance})
        self.cards_updated.emit(cards)
        super().accept()


class AddTransactionDialog(QDialog):
    def __init__(self, transaction_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add {transaction_type}")
        self.transaction_type = transaction_type
        self.transaction = None

        self.layout = QVBoxLayout()

        # Description Input
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(f"Enter {transaction_type.lower()} description")
        self.layout.addWidget(QLabel("Description:"))
        self.layout.addWidget(self.description_input)

        # Amount Input
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText(f"Enter {transaction_type.lower()} amount")
        self.layout.addWidget(QLabel("Amount:"))
        self.layout.addWidget(self.amount_input)

        # Buttons
        self.button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_transaction)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(save_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def save_transaction(self):
        """
        Validate and save the transaction.
        """
        description = self.description_input.text().strip()
        amount_text = self.amount_input.text().strip()

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
            return

        self.transaction = {
            "date": datetime.now().strftime("%d %b %y"),
            "description": description,
            "amount": amount if self.transaction_type == "Income" else -amount,
        }
        self.accept()

    def get_transaction(self):
        """
        Return the saved transaction.
        """
        return self.transaction
