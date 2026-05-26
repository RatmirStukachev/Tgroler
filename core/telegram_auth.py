import hashlib
import hmac
import os
from urllib.parse import parse_qsl

def validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validates the data received from the Telegram Web App.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        if 'hash' not in parsed_data:
            return False

        hash_val = parsed_data.pop('hash')

        # Sort data alphabetically
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])

        # Calculate secret key
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

        # Calculate hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        return calculated_hash == hash_val
    except Exception:
        return False
