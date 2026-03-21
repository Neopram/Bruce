from solders.pubkey import Pubkey

public_key_str = "BKgkwYBDwCc7ZtLJKc7DRFGNsJa6rHE3ANfUFTmAz5J6"
public_key = Pubkey.from_string(public_key_str)

print(public_key)
