# app.py — the target account payment processor stub
import config

def process_payment(amount, account_id):
    return {"status": "processed", "amount": amount, "account_id": account_id}

if __name__ == "__main__":
    print(process_payment(100.00, "ACC-001"))
