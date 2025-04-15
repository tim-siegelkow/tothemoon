#!/usr/bin/env python3
"""
Database Reset Script

This script resets the database by dropping all tables and recreating them.
WARNING: This will delete all data in the database!
"""

import os
import sys
from database.db import reset_db

def main():
    # Confirm with the user
    print("WARNING: This will delete all data in the database!")
    confirmation = input("Are you sure you want to continue? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Reset the database
    print("Resetting database...")
    reset_db()
    print("Database reset successfully!")

if __name__ == "__main__":
    main() 