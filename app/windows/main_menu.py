import logging
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QObject, Signal, QEvent
from app.widgets.menu_bar import AppMenu


class WindowManager(QObject):
    """
    Manages window open and close events across all windows.
    """
    close_all_windows = Signal()

    def __init__(self):
        super().__init__()
        self.window_stack = []  # Stack to keep track of opened windows

    def open_window(self, window):
        """
        Opens a new window and tracks it in the stack.
        """
        if window not in self.window_stack:
            self.window_stack.append(window)
        window.show()
        window.raise_()
        window.activateWindow()

    def close_window(self, window):
        """
        Closes the current window and brings the previous one to the front.
        """
        if window in self.window_stack:
            self.window_stack.remove(window)
            window.close()

        if self.window_stack:
            previous_window = self.window_stack[-1]
            previous_window.raise_()  # Bring the window to the front
            previous_window.activateWindow()


class MainMenu(QMainWindow):
    supports_update_menu = False  # No "Update" menu for MainMenu

    def __init__(self, window_manager):
        super().__init__()
        self.setWindowTitle("Sloth's Finance Tracker")
        self.setGeometry(100, 100, 400, 600)

        self.window_manager = window_manager

        # Shared menu bar
        self.menu_bar = AppMenu(self)
        self.setMenuBar(self.menu_bar)

        # Initialize UI
        self.setup_ui()

    def setup_ui(self):
        """
        Configure the main UI elements.
        """
        # Central widget and layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Title and subtitle
        title_label = QLabel("Sloth's Finance Tracker")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        subtitle_label = QLabel("Manage your finances effortlessly")
        subtitle_label.setObjectName("subtitleLabel")
        layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

        # Buttons for navigation
        buttons = [
            ("Fiat Overview", "fiat", True),
            ("Crypto Overview", "crypto", True),
            ("DeFi Positions", "positions", True),
            ("Settings", "settings", True),
        ]

        for text, window_type, enabled in buttons:
            button = QPushButton(text)
            button.setEnabled(enabled)
            button.setFixedWidth(300)
            button.clicked.connect(lambda _, t=window_type: self.open_window(t))
            layout.addWidget(button, alignment=Qt.AlignCenter)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_window(self, window_type):
        """
        Open a specific window based on the window type.
        """
        try:
            match window_type:
                case "fiat":
                    from app.windows.fiat import FiatDashboard
                    window = FiatDashboard(self.window_manager)
                case "crypto":
                    from app.windows.crypto import CryptoDashboard
                    window = CryptoDashboard(self.window_manager)
                case "positions":
                    from app.windows.positions import PositionTracker
                    window = PositionTracker(self.window_manager)
                case "settings":
                    from app.windows.settings import SettingsDashboard
                    window = SettingsDashboard(self.window_manager)
                case _:
                    raise ValueError(f"Unknown window type: {window_type}")

            # Open the new window
            self.window_manager.open_window(window)
            logging.info(f"Opened window: {window.__class__.__name__}")
        except Exception as e:
            logging.exception(f"Failed to open window '{window_type}': {e}")

    def event(self, event):
        """
        Handle window activation events to dynamically update menus.
        """
        if event.type() == QEvent.WindowActivate:
            logging.debug(f"{self.__class__.__name__} activated: Updating menus.")
            self.menu_bar.dynamic_update_menu()
        return super().event(event)
    
    def closeEvent(self, event):
        self.window_manager.close_all_windows.emit()
        super().closeEvent(event)
