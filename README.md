# Crypto Dashboard

Crypto Dashboard is a desktop application that provides an intuitive interface to track cryptocurrency holdings on Coinbase, DeFi positions (Currently Manual Input), and manage your Income/Expenses (TBA).

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Development](#development)
6. [Project Structure](#project-structure)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

- **Track Coinbase Holdings**: Automatically fetch and display your holdings from Coinbase.
- **DeFi Position Tracking**: Import and analyze DeFi positions from a CSV file.
- **Wallet Balances**: View balances for wallets, including ETH and custom tokens.
- **Custom Filters**: Use dropdown filters for DeFi pools.
- **UI Refresh**: Dynamic menu updates and data refresh with keyboard shortcuts.
- **Settings Management**: Configure wallet addresses, API keys, and UI themes (TBA).
- **Responsive Logging**: Application logs with custom filenames, including date and time.

---

## Installation

### Prerequisites

- Python 3.9+
- `pip` (Python package manager)

### Clone the Repository

```bash
git clone https://github.com/slothmock/sloth_finance_tracker.git
cd sloth_finance_tracker
```

#### Install Dependencies

```bash
Copy code
pip install -r requirements.txt
```

---

## Usage

### Run the Application

```bash
python main.py
```

#### Keyboard Shortcuts

- F5: Refresh active dashboard
- Ctrl+Q: Exit the application

---

## Configuration

### Logging

The application uses a customizable logging setup via settings/logging_config.json.
An example can be seen below and is included in the project.

```json
{
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%H:%M:%S %d-%m-%Y"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app_2024-12-02_15-30-00.log",
            "level": "INFO",
            "formatter": "default"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"]
    }
}
```

#### API Keys

Place API keys in credentials.json:

```json

{
    "coinbase_api_key": "your_api_key",
    "coinbase_api_secret": "your_api_secret",
    "basescan_api_key": "your_api_key"
}
```

---

## Development

### Code Structure

- app/ (Application source code)
- app/widgets/ (Custom PyQt widgets like tables, dialogs, and menus)
- app/windows/ (Main dashboard windows)
- app/helpers/ (Utility and model functions)
- settings/  (Configuration files)

## Project Structure

```plaintext
crypto_dashboard/
├── app/
│   ├── helpers/
│   │   ├── models.py
|   |   ├── proxy_model.py
│   │   ├── strings.py
│   │   └── utils.py
│   ├── widgets/
|   |   ├── __init__.py
│   │   ├── dialogs.py
│   │   ├── menu_bar.py
│   │   ├── status_label.py
│   │   └── table.py
│   ├── windows/
|   |   ├── __init__.py
│   │   ├── crypto.py
│   │   ├── positions.py
│   │   └── settings.py
│   └── app.py
├── logs/ (Created on first app start)
├── settings/
│   ├── credentials.json
│   ├── logging_config.json
│   └── stylesheet.qss
├── user_data/ (Also Created on first app start)
├── main.py
├── README.md
└── requirements.txt
```

---

## Contributing

Contributions/fixes are welcome! Please fork the repository, create a branch for your feature or bug fix, and submit a pull request.

### Development Workflow

1. Fork and clone the repository
2. Create a feature branch
    - ```bash git checkout -b feature-name```
3. Implement your feature
4. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE for more details
