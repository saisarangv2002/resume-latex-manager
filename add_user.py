#!/usr/bin/env python3
"""
Helper script to add new users to the authentication system.
Run: python add_user.py
"""

import bcrypt
import yaml
from pathlib import Path

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def add_user():
    """Interactive script to add a new user."""
    print("\n🔐 Add New User to Resume Manager\n")
    
    username = input("Enter username: ").strip().lower()
    name = input("Enter display name: ").strip()
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    
    if not all([username, name, email, password]):
        print("❌ All fields are required!")
        return
    
    # Hash the password
    hashed = hash_password(password)
    
    # Load existing config
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {
            "credentials": {"usernames": {}},
            "cookie": {
                "expiry_days": 30,
                "key": "resume_latex_interface_secret_key",
                "name": "resume_auth_cookie"
            },
            "preauthorized": {"emails": []}
        }
    
    # Add user
    config["credentials"]["usernames"][username] = {
        "email": email,
        "name": name,
        "password": hashed
    }
    
    # Add to preauthorized emails
    if email not in config.get("preauthorized", {}).get("emails", []):
        if "preauthorized" not in config:
            config["preauthorized"] = {"emails": []}
        config["preauthorized"]["emails"].append(email)
    
    # Save config
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"\n✅ User '{username}' added successfully!")
    print(f"   Name: {name}")
    print(f"   Email: {email}")
    print(f"\nThey can now log in with username '{username}' and their password.")

if __name__ == "__main__":
    add_user()

