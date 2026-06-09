# app.py — Meridian Financial payment processor stub
import config


def process_payment(amount: float, account_id: str) -> dict:
    """Process a payment transaction."""
    return {
        "status": "processed",
        "amount": amount,
        "account_id": account_id,
        "region": config.AWS_REGION,
    }


if __name__ == "__main__":
    result = process_payment(100.00, "ACC-001")
    print(result)
