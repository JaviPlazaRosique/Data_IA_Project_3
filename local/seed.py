"""
Local dev seed — inserts two test users.

Credentials
-----------
  alice@example.com  /  Alice1234!
  bob@example.com    /  Bob1234!

Safe to run multiple times (ON CONFLICT DO NOTHING).
"""

import asyncio
import os
import uuid

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    {
        "id": str(uuid.uuid4()),
        "email": "alice@example.com",
        "username": "alice",
        "full_name": "Alice Test",
        "password": "Alice1234!",
    },
    {
        "id": str(uuid.uuid4()),
        "email": "bob@example.com",
        "username": "bob",
        "full_name": "Bob Test",
        "password": "Bob1234!",
    },
]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        for user in USERS:
            await conn.execute(
                text("""
                    INSERT INTO users
                        (id, email, username, full_name, hashed_password, is_active, is_verified)
                    VALUES
                        (:id, :email, :username, :full_name, :hashed_password, TRUE, TRUE)
                    ON CONFLICT (email) DO NOTHING
                """),
                {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "hashed_password": pwd.hash(user["password"]),
                },
            )
            print(f"  ✓ {user['email']}")
    await engine.dispose()
    print("Seed complete.")


asyncio.run(main())
