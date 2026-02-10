#!/usr/bin/env python3
"""
Initialize DynamoDB Tables for Hamo-UME
Run this script once to create all required tables
"""

from database import create_tables

if __name__ == "__main__":
    print("=" * 60)
    print("Initializing DynamoDB Tables for Hamo-UME")
    print("=" * 60)
    print()

    create_tables()

    print()
    print("=" * 60)
    print("Initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start the server: uvicorn main:app --reload")
    print("2. Check API docs: http://localhost:8000/docs")
    print()
