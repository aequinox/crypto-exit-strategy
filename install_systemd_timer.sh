#!/bin/bash

# Script to install the Crypto Market Monitor systemd service and timer

echo "Installing Crypto Market Monitor systemd service and timer..."

# Create user systemd directory if it doesn't exist
mkdir -p ~/.config/systemd/user/

# Copy service and timer files
cp crypto-monitor.service ~/.config/systemd/user/
cp crypto-monitor.timer ~/.config/systemd/user/

# Reload systemd daemon
systemctl --user daemon-reload

# Enable and start the timer
systemctl --user enable crypto-monitor.timer
systemctl --user start crypto-monitor.timer

# Check status
echo "Checking timer status..."
systemctl --user list-timers | grep crypto-monitor

echo "Installation complete!"
echo "The Crypto Market Monitor will now run at 12:00 AM and 12:00 PM daily."
echo "To check the status of the timer, run: systemctl --user list-timers"
echo "To check the logs, run: journalctl --user -u crypto-monitor.service"
