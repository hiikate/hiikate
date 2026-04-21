#!/usr/bin/env python3
"""One-time OAuth setup — run this once to authorize Gmail access."""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SCRIPT_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "credentials.json")


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERROR: credentials.json not found at {CREDENTIALS_PATH}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Authorization complete. Token saved to {TOKEN_PATH}")
    print("You can now run digest.py — it will not prompt for auth again.")


if __name__ == "__main__":
    main()
