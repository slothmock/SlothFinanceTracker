import logging
from PySide6.QtWidgets import QApplication, QMenuBar, QMessageBox
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from app.widgets.dialogs import UpdateCashDialog, ManageCardsDialog


class AppMenu(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Initialize menus
        self.file_menu = self.addMenu("File")
        self.about_menu = self.addMenu("About")

        # Dynamic menu
        self.update_menu = None

        # Create actions
        self._create_file_menu()
        self._create_about_menu()

    def _create_file_menu(self):
        """
        Add actions to the File menu.
        """
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(QApplication.instance().quit)
        self.file_menu.addAction(exit_action)

    def _create_about_menu(self):
        """
        Add actions to the About menu.
        """
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        self.about_menu.addAction(about_action)

    def dynamic_update_menu(self):
        """
        Dynamically update the "Update" menu based on the active window.
        """
        logging.debug("dynamic_update_menu called")
        active_window = QApplication.activeWindow()
        logging.debug(f"Active window: {active_window}")

        # Ensure the Update menu is removed
        if self.update_menu:
            self.removeAction(self.update_menu.menuAction())
            self.update_menu = None

        # Skip windows that do not support the Update menu
        if not hasattr(active_window, "supports_update_menu") or not active_window.supports_update_menu:
            logging.debug("Active window does not support Update menu.")
            return

        # Create Update menu for supported windows
        logging.debug("Adding Update menu")
        self.update_menu = self.addMenu("Update")

        # Add Refresh action if supported
        if hasattr(active_window, "refresh"):
            refresh_action = QAction("Refresh", self)
            refresh_action.setShortcut("F5")
            refresh_action.triggered.connect(active_window.refresh)
            self.update_menu.addAction(refresh_action)

        # Add specific actions for expense overview
        if getattr(active_window, "supports_update_menu") == "expense_overview":
            self._add_expense_actions()

    def _add_expense_actions(self):
        """
        Add specific actions for the expense overview.
        """
        self.add_action(
            self.update_menu,
            name="Update Cash",
            callback=self.dynamic_call_update_cash,
            tooltip="Update your cash balance.",
        )
        self.add_action(
            self.update_menu,
            name="Manage Cards",
            callback=self.dynamic_call_manage_cards,
            tooltip="Manage your saved cards.",
        )

    def add_action(self, menu, name, callback, shortcut=None, tooltip=None, icon=None):
        """
        Helper method to add an action to a menu.
        """
        action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        if tooltip:
            action.setToolTip(tooltip)
        if icon:
            action.setIcon(QIcon(icon))
        action.triggered.connect(callback)
        menu.addAction(action)

    def dynamic_call_update_cash(self):
        """
        Dynamically call the Update Cash dialog for the active window.
        """
        active_window = QApplication.activeWindow()
        if hasattr(active_window, "open_update_cash_dialog"):
            active_window.open_update_cash_dialog()
        else:
            QMessageBox.critical(self.parent, "Error", "Update Cash is not available for this window.")

    def dynamic_call_manage_cards(self):
        """
        Dynamically call the Manage Cards dialog for the active window.
        """
        active_window = QApplication.activeWindow()
        if hasattr(active_window, "open_manage_cards_dialog"):
            active_window.open_manage_cards_dialog()
        else:
            QMessageBox.critical(self.parent, "Error", "Manage Cards is not available for this window.")

    def show_about_dialog(self):
        """
        Show the About dialog.
        """
        QMessageBox.about(
            self.parent,
            "About",
            "Sloth's Finance Tracker\n\nVersion: 0.1\n"
            "Author: Slothmock\n\nTrack your finances effortlessly!",
        )
