# backend/add_user.py
import argparse
from getpass import getpass
from sqlmodel import Session, select
from pathlib import Path
import sys

from app.auth import users_engine, hash_password, create_users_db_and_tables
from app.models.user import User

def add_user(username: str, password: str, notes: str | None = None, is_active: bool = True):
    create_users_db_and_tables()
    with Session(users_engine) as session:
        # check exists
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            print(f"User '{username}' already exists.")
            return False
        rec = User(username=username, hashed_password=hash_password(password), is_active=is_active)
        session.add(rec)
        session.commit()
        session.refresh(rec)
        print(f"Created user id={rec.id} username={rec.username}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Admin: add user to users.db")
    parser.add_argument("username", help="username (no spaces recommended)")
    parser.add_argument("--password", help="password (if omitted, you will be prompted)")
    parser.add_argument("--notes", help="notes (optional)")
    args = parser.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.")
            sys.exit(2)

    add_user(args.username, password, notes=args.notes)

if __name__ == "__main__":
    main()
