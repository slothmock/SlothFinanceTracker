from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, Qt


class StatusLabel(QLabel):
    """
    A reusable status label for displaying messages with optional timeout and styles.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)  # Default alignment
        self.setObjectName("statusLabel")
        self.clear_message()  # Start with an empty status

    def show_message(self, message, timeout=None, message_type="info"):
        """
        Display a status message with optional styling and timeout.
        
        Args:
            message (str): The message to display.
            timeout (int): Time in milliseconds before the message disappears. None means it stays indefinitely.
            message_type (str): The type of message ("info", "success", "error"). Determines styling.
        """
        self.setText(message)
        self.set_status_style(message_type)
        if timeout:
            QTimer.singleShot(timeout, self.clear_message)

    def set_status_style(self, message_type):
        """
        Set the style of the label based on the message type.
        
        Args:
            message_type (str): The type of message ("info", "success", "error").
        """
        if message_type == "success":
            self.setStyleSheet("color: green; font-weight: bold;")
        elif message_type == "error":
            self.setStyleSheet("color: red; font-weight: bold;")
        else:  # Default to "info"
            self.setStyleSheet("color: black; font-weight: normal;")

    def show_error(self, message, timeout=None):
        """
        Display an error message with styling.
        
        Args:
            message (str): The error message to display.
            timeout (int): Time in milliseconds before the message disappears. None means it stays indefinitely.
        """
        self.show_message(message, timeout, message_type="error")

    def clear_message(self):
        """
        Clear the current status message and reset styling.
        """
        self.setText("")
        self.setStyleSheet("")  # Reset to default styling
