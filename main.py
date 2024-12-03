import asyncio, logging, logging.config, json
from qasync import QEventLoop
from datetime import datetime

from PySide6.QtWidgets import QApplication

from app.windows.main_menu import MainMenu, WindowManager
from app.helpers.utils import load_stylesheet


async def main():
    """
    Main entry point for the application.
    """
    logging.info("App Initialising...")

    # Create the QApplication and QEventLoop
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Load and apply the stylesheet asynchronously
    try:
        stylesheet = await load_stylesheet("settings/style.qss")
        app.setStyleSheet(stylesheet)
        logging.info("Stylesheet applied.")
    except Exception as e:
        logging.error(f"Failed to load stylesheet: {e}")

    # Init WindowManager
    window_manager = WindowManager()
    logging.info("WindowManager Initialised...")

    # Show the Main Menu
    main_menu = MainMenu(window_manager)
    
    main_menu.show()
    logging.info("MainMenu displayed.")

    # Run the QEventLoop
    with loop:
        loop.run_forever()


def init_logger():
    """
    Initialize logging configuration with dynamic filename.
    """
    try:
        # Load the logging configuration
        with open("settings/logging_config.json", "r") as config_file:
            config = json.load(config_file)

        # Generate a dynamic log filename with date and time
        log_filename = datetime.now().strftime("logs/app_%Y-%m-%d_%H-%M-%S.log")
        
        # Ensure the log directory exists
        import os
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)

        # Update the filename in the file handler
        config["handlers"]["file"]["filename"] = log_filename

        # Adjust logging level based on APP_MODE
        app_mode = "DEBUG"
        if app_mode == "DEBUG":
            config["root"]["level"] = "DEBUG"
        else:
            config["root"]["level"] = "INFO"

        # Apply the logging configuration
        logging.config.dictConfig(config)
        logging.info(f"Application started in {app_mode} mode with log file: {log_filename}")

    except Exception as e:
        logging.error(f"Failed to initialize logging: {e}")
        raise


if __name__ == "__main__":
    init_logger()
    asyncio.run(main())
