#!/usr/bin/env python3
"""Daily email digest: fetches last 24h of Gmail, ranks top 3-5, sends summary."""

import os
import base64
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import anthropic
from anthropic.types import TextBlock

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SCRIPT_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "credentials.json")
MY_EMAIL = "kate@edge8.co"


def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_recent_messages(service):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    after_epoch = int(since.timestamp())
    query = f"after:{after_epoch} -category:promotions -category:social"

    result = service.users().messages().list(
        userId="me", q=query, maxResults=50
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me", messageId=msg["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        snippet = full.get("snippet", "")
        date = headers.get("Date", "")
        sender = headers.get("From", "")
        subject = headers.get("Subject", "(no subject)")

        emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "date": date,
            "snippet": snippet,
        })

    return emails


def summarize_with_claude(emails):
    if not emails:
        return "No new emails in the past 24 hours."

    email_list = "\n\n".join(
        f"[{i+1}] From: {e['from']}\n"
        f"    Subject: {e['subject']}\n"
        f"    Date: {e['date']}\n"
        f"    Preview: {e['snippet']}"
        for i, e in enumerate(emails)
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""You are helping Kate review her inbox. Here are her emails from the past 24 hours:

{email_list}

Pick the 3–5 most important messages she needs to act on or be aware of today.
Rank by urgency and sender importance (clients, deadlines, direct questions, time-sensitive items first).

Write a plain-language briefing — no bullet-point walls, just short paragraphs she can read in 60 seconds.
For each item: who it's from, what they want or what happened, and whether she needs to respond or just knows.
End with a one-line "Today's priority" sentence."""
        }]
    )
    block = response.content[0]
    if not isinstance(block, TextBlock):
        raise ValueError(f"Unexpected response block type: {type(block)}")
    return block.text


def send_digest(service, summary):
    today = datetime.now().strftime("%A, %B %-d")
    subject = f"Your morning digest — {today}"
    body = f"Good morning, Kate.\n\n{summary}\n\n---\nSent by your daily email digest."

    message = MIMEText(body)
    message["to"] = MY_EMAIL
    message["from"] = MY_EMAIL
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print(f"Digest sent to {MY_EMAIL}")


def main():
    service = get_gmail_service()
    print("Fetching emails from the past 24 hours...")
    emails = fetch_recent_messages(service)
    print(f"Found {len(emails)} emails. Summarizing...")
    summary = summarize_with_claude(emails)
    print("Sending digest...")
    send_digest(service, summary)


if __name__ == "__main__":
    main()
