import pyotp

def generate_totp(secret):
    """
    Generates a 6-digit TOTP for broker authentication (e.g., Kotak Neo).
    """
    if not secret:
        return None
    totp = pyotp.TOTP(secret)
    return totp.now()

if __name__ == "__main__":
    # Example
    # print(generate_totp("JBSWY3DPEHPK3PXP"))
    pass
