import aiofiles, aiohttp, json, os, asyncio, logging, re

from app.helpers.strings import CREDENTIALS_FILE, SETTINGS_FILE

async def fetch_crypto_price(crypto: str, fiat: str = "USD") -> float:
    """
    Fetch the current price of a cryptocurrency in a specified fiat currency.
    Args:
        crypto (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
        fiat (str): The fiat currency symbol (e.g., 'USD', 'EUR'). Default is 'USD'.
    Returns:
        float: The current price of the cryptocurrency.
    """
    try:
        url = f"https://api.coinbase.com/v2/prices/{crypto}-{fiat}/spot"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"Error fetching price for {crypto}-{fiat}: {response.status}")
                    return 0.0
                data = await response.json()
                return float(data["data"]["amount"])
    except Exception as e:
        logging.exception(f"Error fetching crypto price for {crypto}-{fiat}: {e}")
        return 0.0


def parse_float(value, default=0.0) -> float:
    """
    Safely parse a value as a float, handling strings with special characters like '$', ',', or spaces.
    
    Args:
        value: The value to parse.
        default: The default value to return if parsing fails.
        
    Returns:
        float: The parsed float or the default value.
    """
    if isinstance(value, str):
        # Remove non-numeric characters (except '.' and '-')
        value = re.sub(r"[^\d\.-]", "", value)
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# Stylesheet Management
async def load_stylesheet(filepath: str) -> str:
    """
    Load the stylesheet asynchronously.
    Args:
        filepath (str): Path to the stylesheet file.
    Returns:
        str: The content of the stylesheet.
    """
    return await asyncio.to_thread(_sync_load_stylesheet, filepath)

def _sync_load_stylesheet(filepath: str) -> str:
    """
    Synchronous helper to load a stylesheet.
    Args:
        filepath (str): Path to the stylesheet file.
    Returns:
        str: The content of the stylesheet.
    """
    try:
        with open(filepath, "r") as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error loading stylesheet from {filepath}: {e}")
        return ""


# General Settings Management
async def load_settings() -> dict:
    """
    Load general settings from the JSON file.
    Returns:
        dict: Settings data.
    """
    try:
        if not os.path.exists(SETTINGS_FILE):
            logging.warning(f"Settings file '{SETTINGS_FILE}' not found. Creating default settings.")
            default_settings = {
                "eth_address": "",
                "sol_address": "",
                "theme": "light",
                "watchlist": []
            }
            await save_settings(default_settings)
            return default_settings

        async with aiofiles.open(SETTINGS_FILE, "r") as file:
            content = await file.read()
            return json.loads(content)

    except Exception as e:
        logging.exception(f"Error loading settings: {e}")
        return {}

async def save_settings(settings: dict) -> None:
    """
    Save general settings to the JSON file.
    Args:
        settings (dict): Settings data to save.
    """
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        async with aiofiles.open(SETTINGS_FILE, "w") as file:
            await file.write(json.dumps(settings, indent=4))
        logging.info("Settings saved successfully.")
    except Exception as e:
        logging.exception(f"Error saving settings: {e}")


# Credentials Management
async def load_credentials() -> dict:
    """
    Load API credentials from the JSON file.
    Returns:
        dict: Credentials data.
    """
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            logging.warning(f"Credentials file '{CREDENTIALS_FILE}' not found. Creating default credentials.")
            default_credentials = {
                "coinbase_api_key": "",
                "coinbase_api_secret": "",
                "basescan_api_key": ""
            }
            await save_credentials(default_credentials)
            return default_credentials

        async with aiofiles.open(CREDENTIALS_FILE, "r") as file:
            content = await file.read()
            return json.loads(content)

    except Exception as e:
        logging.exception(f"Error loading credentials: {e}")
        return {}

async def save_credentials(credentials: dict) -> None:
    """
    Save API credentials to the JSON file.
    Args:
        credentials (dict): Credentials data to save.
    """
    try:
        os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
        async with aiofiles.open(CREDENTIALS_FILE, "w") as file:
            await file.write(json.dumps(credentials, indent=4))
        logging.info("Credentials saved successfully.")
    except Exception as e:
        logging.exception(f"Error saving credentials: {e}")