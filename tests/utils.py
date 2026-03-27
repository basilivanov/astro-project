# ############################################################################
# AI_HEADER: TEST_UTILS
# ROLE: Utilities for generating valid Telegram auth data for testing.
############################################################################

import hashlib
import hmac
import json
import time
from urllib.parse import quote

def sign_init_data(user_data: dict, bot_token: str, **kwargs) -> str:
    """
    # PURPOSE: Generate a valid signed initData string.
    # INPUT: user_data dict, bot_token, extra params (start_param, etc).
    # OUTPUT: initData string (e.g. "user=...&hash=...").
    """
    data_list = []
    
    # Add user field. Telegram initData transport is urlencoded, and the
    # backend validates against parse_qsl-decoded values, so tests should sign
    # the decoded payload but transport the encoded one.
    user_json = json.dumps(user_data, separators=(',', ':'))
    data_list.append(f"user={user_json}")
    
    # Add auth_date
    auth_date = str(int(time.time()))
    data_list.append(f"auth_date={auth_date}")
    
    # Add extra params
    for key, value in kwargs.items():
        data_list.append(f"{key}={value}")
    
    # Sort alphabetically (required for signing)
    data_list.sort()
    data_check_string = "\n".join(data_list)
    
    # Calculate Hash
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Construct final string (order doesn't matter for transport, but usually user comes first)
    # We must join them with &
    # Note: values should be url-encoded in a real scenario if they contain special chars,
    # but for basic tests simple join is often enough if data is simple.
    
    # Let's reconstruct the list with hash
    final_pairs = []
    for item in data_list:
        key, value = item.split("=", 1)
        final_pairs.append(f"{key}={quote(value, safe='')}" )
    final_pairs.append(f"hash={hash_value}")

    return "&".join(final_pairs)
