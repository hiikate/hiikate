#!/usr/bin/env bash
# Run this once on your machine to wire up the daily digest.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Email Digest Setup ==="

# 1. Copy systemd units
mkdir -p ~/.config/systemd/user
cp "$SCRIPT_DIR"/../../../.config/systemd/user/email-digest.service ~/.config/systemd/user/
cp "$SCRIPT_DIR"/../../../.config/systemd/user/email-digest.timer ~/.config/systemd/user/

# Update the service to use the actual script path
sed -i "s|/home/user/hiikate|$SCRIPT_DIR|g" ~/.config/systemd/user/email-digest.service

# 2. Write env file if it doesn't exist
mkdir -p ~/.config/email-digest
if [ ! -f ~/.config/email-digest/env ]; then
    touch ~/.config/email-digest/env
    chmod 600 ~/.config/email-digest/env
fi

# 3. Prompt for ANTHROPIC_API_KEY
if ! grep -q "ANTHROPIC_API_KEY" ~/.config/email-digest/env 2>/dev/null; then
    read -rsp "Paste your Anthropic API key: " apikey
    echo
    echo "ANTHROPIC_API_KEY=$apikey" >> ~/.config/email-digest/env
    echo "API key saved to ~/.config/email-digest/env (chmod 600)"
fi

# 4. Enable and start timer
systemctl --user daemon-reload
systemctl --user enable email-digest.timer
systemctl --user start email-digest.timer
systemctl --user status email-digest.timer --no-pager

echo ""
echo "=== Next: authorize Gmail ==="
echo "Run: python3 $SCRIPT_DIR/auth_setup.py"
echo "Then test with: python3 $SCRIPT_DIR/digest.py"
