"""Demo seeder: Create a secure access token for testing.

Run from the backend directory:
    python scripts/seed_secure_token.py

Creates a secure access token for user ID 1 with PIN 1234.
Prints the secure URL to use for testing.
"""

from __future__ import annotations

import sys
import os

# Add the project root to the path so we can import the app package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.secure_financial_intelligence_service import SecureFinancialIntelligenceService


def main() -> None:
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    pin = sys.argv[2] if len(sys.argv) > 2 else "1234"
    hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24

    db = SessionLocal()
    try:
        svc = SecureFinancialIntelligenceService(db)
        record = svc.create_token(user_id=user_id, pin=pin, expires_hours=hours)

        print("\n" + "=" * 60)
        print("  SECURE FINANCIAL INTELLIGENCE — DEMO TOKEN CREATED")
        print("=" * 60)
        print(f"\n  User ID:      {user_id}")
        print(f"  PIN:          {pin}")
        print(f"  Token:        {record.token}")
        print(f"  Expires:      {record.expires_at.isoformat()}")
        print(f"\n  Test URL (dev):")
        print(f"  http://localhost:5173/secure-fi/{record.token}")
        print(f"\n  API validate:")
        print(f"  POST http://localhost:8000/api/v1/secure-fi/validate")
        print(f"  Body: {{\"token\": \"{record.token}\"}}")
        print("\n" + "=" * 60 + "\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
