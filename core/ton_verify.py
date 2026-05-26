import requests

def verify_ton_transaction(boc: str, expected_address: str, expected_amount_nano: int) -> bool:
    """
    Very basic mock/stub for TON verification for the sake of the exercise.
    In a true production app, you would decode the BOC or query a TON API
    (like Toncenter or TonAPI) using the transaction hash to ensure the money
    was sent to `expected_address` with `expected_amount_nano`.
    """
    if not boc:
        return False
    # Example logic using TonAPI (commented out as we don't have an API key here):
    # response = requests.get(f"https://tonapi.io/v2/blockchain/transactions/{boc}")
    # data = response.json()
    # return data.get('in_msg', {}).get('value') == expected_amount_nano ...

    # Since we can't reliably test real blockchain verification in this sandbox,
    # we enforce that a BOC is provided as a placeholder.
    return True
