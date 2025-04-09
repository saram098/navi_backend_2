#!/usr/bin/env python3
"""
Script to check if all required environment variables are set.
Run this script before starting the application to ensure all required
environment variables are available.
"""

import os
import sys

required_vars = [
    "MONGO_URI",
    "SECRET_KEY",
    "STRIPE_SECRET_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER", 
    "OPENAI_API_KEY"
]

optional_vars = [
    "REPLIT_DB_URL",
    "PORT",
    "HOST",
]

def check_env():
    """Check if all required environment variables are set."""
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set these variables before starting the application.")
        return False
    
    print("✅ All required environment variables are set!")
    
    # Check optional vars
    missing_optional = []
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
    
    if missing_optional:
        print(f"ℹ️ Note: Some optional environment variables are not set: {', '.join(missing_optional)}")
    
    return True

def main():
    """Main function."""
    success = check_env()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()